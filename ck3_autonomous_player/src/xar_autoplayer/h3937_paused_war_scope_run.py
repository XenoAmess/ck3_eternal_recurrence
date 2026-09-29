"""H3937 phase-0 paused native war roster observation, with no gameplay step.

This is a static, disabled candidate.  Its eventual result is evidence for a
separate decision, never date, movement, attack, or spending authorization.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import threading
import time

from .bridge.native_driver import NativeHeadlessGameplayDriver, _route_contact_hostile_ids
from .bridge.service import GameplayBridgeService
from .environment import EnvironmentSpec, ensure_state_path_safe
from .errors import AgentError
from .h3937_stationary_route_contact_query_run import (
    ARMY_ID, CHECKPOINT_SHA256, CHILD_PENDING_SIDECAR_SHA256,
    DLL_SHA256, EXPECTED_DATE_RAW, EXPECTED_EPISODE_RUN_ID,
    EXPECTED_HISTORY_INDEX, INJECTOR_SHA256, ROUND_PATTERN,
    _cold_restore_bookkeeping, _command_history, _exact_prepared_rebind,
    _positive_seconds, _query_history_unchanged, _read_driver_state,
    _same_frame, _sha256, _snapshot_history,
)
from .native_auto_run import (
    READINESS_POLL_SECONDS, READINESS_STABLE_SECONDS,
    SESSION_TIMEOUT_GRACE_SECONDS, _cleanup_report, _public_binding,
    _wait_for_readiness,
)
from .native_session import native_session, validate_cold_start_checkpoint_for_pipe
from .runtime import (
    NativeBridgeLaunchConfig, native_bridge_launch_config_from_environment,
    utc_now, validate_native_bridge_launch_config,
)


# Neither a source offer nor a prior H3928 query grants this checkout a launch.
H3937_PHASE0_LIVE_AUTHORIZED = False
WAR_ID = 16777231
TARGET_PROVINCE_ID = 2610
MAX_HOSTILES = 64
_STATE_CODES = {
    1: "regular", 2: "combat", 3: "sieging", 4: "embarked",
    5: "gathering", 6: "retreating", 7: "moving", 8: "raiding",
    9: "bartering",
}


def _positive_id(value: object) -> bool:
    return type(value) is int and 0 < value <= 2**31 - 1


def _read_rebind_receipt_and_sha(path: Path) -> tuple[dict[str, object], str]:
    try:
        raw = path.read_bytes()
        parsed = json.loads(raw.decode("utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"cannot read exact H3937 rebind receipt: {error}") from error
    if not isinstance(parsed, dict):
        raise AgentError("H3937 rebind receipt is not an object")
    return parsed, hashlib.sha256(raw).hexdigest().upper()


def _checkout_commit() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=Path(__file__).resolve().parents[3],
            capture_output=True, text=True, check=True, timeout=10)
    except (OSError, subprocess.SubprocessError) as error:
        raise AgentError(f"H3937 phase-0 producer checkout identity unavailable: {error}") from error
    commit = completed.stdout.strip()
    if len(commit) not in (40, 64) or any(char not in "0123456789abcdefABCDEF" for char in commit):
        raise AgentError("H3937 phase-0 producer checkout identity malformed")
    return commit.lower()


def _exact_phase0_subject(frame: object) -> bool:
    """Check the fixed save/actor/war/army without presuming an enemy roster."""
    if not isinstance(frame, dict):
        return False
    wars = frame.get("active_wars")
    armies = frame.get("player_armies")
    played = frame.get("played_character")
    if not (isinstance(wars, list) and len(wars) == 1
            and isinstance(armies, list) and isinstance(played, dict)):
        return False
    war = wars[0]
    controllable = [row for row in armies
                    if isinstance(row, dict) and row.get("controllable") is True]
    return bool(
        frame.get("paused") is True
        and frame.get("map_ready") is True
        and frame.get("date_raw") == EXPECTED_DATE_RAW
        and frame.get("episode_run_id") == EXPECTED_EPISODE_RUN_ID
        and frame.get("episode_character_id") == 29829
        and played.get("character_id") == 29829
        and isinstance(war, dict) and war.get("war_id") == WAR_ID
        and war.get("player_side") == "defender"
        and isinstance(war.get("enemy_armies"), list)
        and isinstance(war.get("allied_armies"), list)
        and len(controllable) == 1
        and controllable[0].get("army_id") == ARMY_ID
        and controllable[0].get("current_province_id") == TARGET_PROVINCE_ID
        and frame.get("active_event") is None and "active_event" in frame
        and frame.get("pending_character_interaction") is None
        and "pending_character_interaction" in frame
    )


def _army_scope_row(row: object) -> dict[str, object] | None:
    if not isinstance(row, dict):
        return None
    route = row.get("route_province_ids")
    state = row.get("army_state")
    if not (
        _positive_id(row.get("army_id"))
        and _positive_id(row.get("owner_character_id"))
        and _positive_id(row.get("current_province_id"))
        and isinstance(route, list) and len(route) <= 4096
        and all(_positive_id(province) for province in route)
        and "move_target_province_id" in row
        and (row["move_target_province_id"] is None
             or _positive_id(row["move_target_province_id"]))
        and isinstance(row.get("move_target_observable"), bool)
        and (
            (not route and row["move_target_province_id"] is None
             and row["move_target_observable"] is False)
            or (bool(route) and row["move_target_observable"] is True
                and row["move_target_province_id"] == route[-1])
        )
        and isinstance(state, str) and state and state != "unknown"
        and type(row.get("army_state_code")) is int
        and _STATE_CODES.get(row["army_state_code"]) == state
        and isinstance(row.get("in_combat"), bool)
        and isinstance(row.get("retreating"), bool)
        and isinstance(row.get("controllable"), bool)
        and (bool(route) or state in {"regular", "sieging", "combat"})
    ):
        return None
    return {key: copy.deepcopy(row.get(key)) for key in (
        "army_id", "owner_character_id", "current_province_id",
        "move_target_province_id", "move_target_observable",
        "route_province_ids", "army_state", "army_state_code",
        "in_combat", "retreating", "controllable",
    )}


def _phase0_scope(frame: object) -> dict[str, object] | None:
    """Project every native-published enemy, with a dynamic query-eligible set."""
    if not _exact_phase0_subject(frame):
        return None
    assert isinstance(frame, dict)
    war = frame["active_wars"][0]
    raw_enemies = war["enemy_armies"]
    raw_allies = war["allied_armies"]
    raw_players = frame["player_armies"]
    if not (1 <= len(raw_enemies) <= MAX_HOSTILES
            and len(raw_allies) + len(raw_players) <= 64):
        return None
    enemies = [_army_scope_row(row) for row in raw_enemies]
    allies = [_army_scope_row(row) for row in raw_allies]
    players = [_army_scope_row(row) for row in raw_players]
    if any(row is None for row in (*enemies, *allies, *players)):
        return None
    if sum(len(row["route_province_ids"])
           for row in (*enemies, *allies, *players)) > 4096:
        return None
    enemy_ids = [row["army_id"] for row in enemies]
    ally_ids = [row["army_id"] for row in allies]
    player_ids = [row["army_id"] for row in players]
    if (len(set(enemy_ids)) != len(enemy_ids)
            or len(set(ally_ids)) != len(ally_ids)
            or len(set(player_ids)) != len(player_ids)
            or set(enemy_ids) & (set(ally_ids) | set(player_ids))):
        return None
    # The native war row intentionally repeats the player's own CUnit in
    # allied_armies.  A duplicate across those two groups is admissible only
    # when every observed field agrees; all other duplicate IDs fail closed.
    player_by_id = {row["army_id"]: row for row in players}
    if any(row["army_id"] in player_by_id
           and row != player_by_id[row["army_id"]] for row in allies):
        return None
    controllable_ids = {
        row["army_id"] for row in (*allies, *players)
        if row["controllable"] is True
    }
    if controllable_ids != {ARMY_ID}:
        return None
    if any(row["controllable"] is not False for row in enemies):
        return None
    if any(row["army_id"] == ARMY_ID for row in enemies):
        return None
    expected_query_ids = tuple(sorted(
        row["army_id"] for row in enemies
        if not row["retreating"] and row["army_state"] != "retreating"
        and row["army_state_code"] != 6
    ))
    if not expected_query_ids or _route_contact_hostile_ids(frame) != expected_query_ids:
        return None
    objective_states = war.get("objective_province_states")
    target_states = ([row for row in objective_states
                      if isinstance(row, dict)
                      and row.get("province_id") == TARGET_PROVINCE_ID]
                     if isinstance(objective_states, list) else [])
    if len(target_states) > 1:
        return None
    target_state = target_states[0] if target_states else None
    occupancy = (
        copy.deepcopy(target_state)
        if isinstance(target_state, dict)
        and target_state.get("occupation_observable") is True
        else "not_observed"
    )
    return {
        "war_id": WAR_ID,
        "player_side": "defender",
        "player_armies": players,
        "allied_armies": allies,
        "enemy_armies": enemies,
        "all_hostile_army_ids": sorted(enemy_ids),
        "query_eligible_hostile_army_ids": list(expected_query_ids),
        "province_2610_occupation": occupancy,
        "snapshot_scope": "native_published_observable_armies",
        "complete_physical_army_inventory_proven": False,
        "route_read_completeness_proven": False,
        "date_advance_authorized": False,
    }


def collect_h3937_paused_war_scope_once(
    spec: EnvironmentSpec, *, timeout_seconds: float = 390,
    readiness_timeout_seconds: float = 300,
    readiness_stable_seconds: float = READINESS_STABLE_SECONDS,
    poll_interval_seconds: float = READINESS_POLL_SECONDS,
    ownership_round_id: str, cold_start_checkpoint: bool = False,
    native_bridge: NativeBridgeLaunchConfig | None = None,
) -> dict[str, object]:
    """One bounded managed native session, two snapshots, zero commands."""
    if H3937_PHASE0_LIVE_AUTHORIZED is not True:
        raise AgentError("H3937 phase-0 only: new official pair/screen review and launch authorization absent")
    timeout = _positive_seconds(timeout_seconds, "timeout_seconds")
    readiness_timeout = _positive_seconds(
        readiness_timeout_seconds, "readiness_timeout_seconds")
    stable_seconds = float(readiness_stable_seconds)
    poll_seconds = _positive_seconds(poll_interval_seconds, "poll_interval_seconds")
    if stable_seconds < 0 or ROUND_PATTERN.fullmatch(ownership_round_id) is None:
        raise AgentError("H3937 phase-0 requires stable readiness and monotonic round")
    if cold_start_checkpoint is not True:
        raise AgentError("H3937 phase-0 requires exact cold-start checkpoint")
    config = (native_bridge_launch_config_from_environment() if native_bridge is None
              else validate_native_bridge_launch_config(native_bridge))
    if config is None or config.mode != "native-headless":
        raise AgentError("H3937 phase-0 requires native-headless")
    ensure_state_path_safe(spec.state_dir)
    checkpoint = validate_cold_start_checkpoint_for_pipe(spec, config.pipe_name)
    save_path = spec.profile_dir / "save games" / "xar_checkpoint.ck3"
    driver_path = spec.state_dir / "native-session" / "driver-state.json"
    sidecar_path = spec.state_dir / "player-child-matrilineal-formal-v1.json"
    receipt_path = spec.state_dir / "ordinary-seed-rebind-v1.json"
    driver_before = _read_driver_state(driver_path)
    receipt, receipt_sha256 = _read_rebind_receipt_and_sha(receipt_path)
    lifecycle = checkpoint.get("succession_lifecycle")
    driver_checkpoint = driver_before.get("last_checkpoint")
    environment_sha256 = (lifecycle.get("environment_sha256")
                          if isinstance(lifecycle, dict) else None)
    paths = {"checkpoint": save_path, "driver_state": driver_path,
             "child_pending_sidecar": sidecar_path, "bridge_dll": config.dll_path,
             "bridge_injector": config.injector_path,
             "rebind_receipt": receipt_path, "producer_module": Path(__file__)}
    before_hashes = {key: _sha256(path) for key, path in paths.items()}
    checkout_before = _checkout_commit()
    if not (
        before_hashes["checkpoint"].casefold() == CHECKPOINT_SHA256.casefold()
        and before_hashes["child_pending_sidecar"].casefold()
        == CHILD_PENDING_SIDECAR_SHA256.casefold()
        and before_hashes["bridge_dll"].casefold() == DLL_SHA256.casefold()
        and before_hashes["bridge_injector"].casefold() == INJECTOR_SHA256.casefold()
        and before_hashes["rebind_receipt"] == receipt_sha256
        and _exact_prepared_rebind(
            receipt, prepared_driver_sha256=before_hashes["driver_state"],
            pipe_name=config.pipe_name, state_dir=spec.state_dir,
            profile_dir=spec.profile_dir, environment_sha256=environment_sha256 or "")
        and checkpoint.get("saved_date_raw") == EXPECTED_DATE_RAW
        and checkpoint.get("history_index") == EXPECTED_HISTORY_INDEX
        and driver_before.get("episode_run_id") == EXPECTED_EPISODE_RUN_ID
        and driver_before.get("episode_character_id") == 29829
        and isinstance(driver_checkpoint, dict)
        and driver_checkpoint.get("episode_run_id") == EXPECTED_EPISODE_RUN_ID
        and driver_checkpoint.get("episode_character_id") == 29829
        and driver_checkpoint.get("history_index") == EXPECTED_HISTORY_INDEX
        and str(driver_checkpoint.get("sha256", "")).casefold()
        == CHECKPOINT_SHA256.casefold()
        and isinstance(lifecycle, dict)
        and lifecycle.get("xar_enabled") == "xar_off"
        and lifecycle.get("lifecycle") == "ordinary_campaign_succession"
        and lifecycle.get("pact_contract")
        == "absent_by_fresh_campaign_xar_off_contract"
    ):
        raise AgentError("H3937 phase-0 source/prepared identity differs; launch refused")

    started_at = utc_now()
    started = time.monotonic()
    deadline = started + timeout
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    driver: NativeHeadlessGameplayDriver | None = None
    thread: threading.Thread | None = None
    driver_closed = False
    readiness = before = after = None
    primary_error: str | None = None

    def supervise() -> None:
        try:
            session_state["report"] = native_session(
                spec, timeout_seconds=timeout + SESSION_TIMEOUT_GRACE_SECONDS,
                native_bridge=config, input_stream=None, output_stream=None,
                poll_interval_seconds=poll_seconds, cold_start_checkpoint=True,
                stop_event=stop_event, prepared_xar_enabled="xar_off")
        except BaseException as error:
            session_state["error"] = f"{type(error).__name__}: {error}"
        finally:
            session_done.set()

    try:
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name, state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games")
        service = GameplayBridgeService(driver)
        thread = threading.Thread(target=supervise,
                                  name="xar-h3937-phase0-roster-session", daemon=False)
        thread.start()
        readiness = _wait_for_readiness(
            driver, session_done=session_done, session_state=session_state,
            timeout_seconds=min(readiness_timeout,
                                max(0.001, deadline - time.monotonic())),
            stable_seconds=stable_seconds, poll_interval_seconds=poll_seconds,
            cold_start_checkpoint=True, allow_terminal=False,
            require_post_ready_pump=True)
        if time.monotonic() >= deadline:
            raise AgentError("H3937 phase-0 timeout before native snapshot")
        before = service.snapshot()
        if not _exact_phase0_subject(before):
            raise AgentError("H3937 phase-0 exact paused subject unavailable")
        after = service.snapshot()
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        stop_started = time.monotonic()
        stop_event.set()
        if thread is not None:
            thread.join()
        stop_elapsed = round(max(0.0, time.monotonic() - stop_started), 3)
        if driver is not None:
            try:
                driver.close()
                driver_closed = True
            except BaseException as error:
                primary_error = f"{primary_error or ''}; close: {error}"

    cleanup = _cleanup_report(session_state.get("report"),
                              session_error=session_state.get("error"),
                              driver_closed=driver_closed, elapsed_seconds=stop_elapsed)
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(session_state.get("error") or cleanup.get("reason")
                            or "managed cleanup unproven")
    try:
        after_hashes = {key: _sha256(path) for key, path in paths.items()}
        driver_after = _read_driver_state(driver_path)
        checkout_after = _checkout_commit()
    except (OSError, AgentError) as error:
        after_hashes = {}
        driver_after = None
        checkout_after = None
        primary_error = primary_error or f"{type(error).__name__}: {error}"
    before_scope = _phase0_scope(before)
    after_scope = _phase0_scope(after)
    restore = _cold_restore_bookkeeping(driver_before, before, checkpoint)
    checks = {
        "exact_paused_subject": _exact_phase0_subject(before),
        "native_published_roster_well_formed": before_scope is not None,
        "readiness_bound_to_snapshot": _same_frame(readiness, before),
        "single_cold_restore_bookkeeping": restore.get("exact") is True,
        "same_paused_frame": _same_frame(before, after),
        "war_roster_unchanged": before_scope is not None and before_scope == after_scope,
        "zero_appended_queries": _query_history_unchanged(before, after),
        "date_unchanged": isinstance(before, dict) and isinstance(after, dict)
        and before.get("date_raw") == after.get("date_raw") == EXPECTED_DATE_RAW,
        "persisted_history_matches_snapshot": bool(
            after is not None and driver_after is not None
            and _command_history(driver_after) == _snapshot_history(after)),
        "assets_unchanged": bool(after_hashes and all(
            before_hashes[key] == after_hashes[key] for key in
            ("checkpoint", "child_pending_sidecar", "bridge_dll",
             "bridge_injector", "rebind_receipt", "producer_module"))),
        "producer_checkout_unchanged": checkout_after == checkout_before,
        "cleanup_proven": cleanup.get("ok") is True,
    }
    ok = primary_error is None and all(checks.values())
    return {
        "schema": "xar.ck3.h3937-paused-war-scope-phase0-v1",
        "ok": ok, "status": "GREEN_READ_ONLY_ROSTER" if ok else "RED",
        "action_authorized": False, "date_advance_authorized": False,
        "gameplay_actions": 0, "query_actions": 0,
        "round": ownership_round_id, "started_at": started_at,
        "finished_at": utc_now(),
        "source": {"save_sha256": before_hashes["checkpoint"],
                   "prepared_driver_sha256": before_hashes["driver_state"],
                   "rebind_receipt_sha256": receipt_sha256,
                   "producer_module_sha256": before_hashes["producer_module"],
                   "producer_checkout_commit": checkout_before},
        "asset_sha256_before": before_hashes,
        "asset_sha256_after": after_hashes,
        "readiness": _public_binding(readiness) if isinstance(readiness, dict) else None,
        "frame": {**{key: before.get(key) for key in (
            "snapshot_id", "revision", "native_revision", "date_raw",
            "episode_run_id", "episode_character_id", "paused", "map_ready")},
            "connection_generation": (
                before.get("diagnostics", {}).get("connection_generation")
                if isinstance(before.get("diagnostics"), dict)
                else before.get("connection_generation"))}
            if isinstance(before, dict) else None,
        "scope": before_scope, "checks": checks, "cleanup": cleanup,
        "error": primary_error,
    }
