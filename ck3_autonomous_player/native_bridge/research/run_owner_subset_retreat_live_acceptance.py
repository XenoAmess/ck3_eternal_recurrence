#!/usr/bin/env python3
"""Materialize and execute the mixed-owner active-retreat fixture.

The source battle save is immutable.  A production-only managed launch first
advances the original player to day 15 and saves.  A second seed-only launch
temporarily mounts the repository's development ``mod_bridge`` and publishes
a guarded ``set_player_character`` effect through its atomically replaced run
inbox.  Its save bytes are then copied twice into freshly prepared
production-only profiles: the first launch rebinds the new one-life identity
and writes a canonical checkpoint; the second launch proves that checkpoint
cold-loads before it submits the real owner-subset retreat through the
production native bridge.

No visual input, taskkill, Stop-Process, or combat constructor is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import time
from typing import Any, Callable
import uuid


RESEARCH_ROOT = Path(__file__).resolve().parent
PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(RESEARCH_ROOT))
sys.path.insert(0, str(PACKAGE_ROOT))

import run_active_combat_retreat_live_acceptance as retreat_live  # noqa: E402
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.mod_driver import DataModGameplayDriver  # noqa: E402
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.environment import (  # noqa: E402
    ensure_state_path_safe,
    is_relative_to,
    make_spec,
    paths_overlap,
    prepare_profile,
    verify_profile,
    write_json_atomic,
    write_text_atomic,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.locking import (  # noqa: E402
    exclusive_launch_lock,
    exclusive_state_lock,
)
from xar_autoplayer.native_auto_run import (  # noqa: E402
    _cleanup_report,
    _compact_session_report,
    _wait_for_readiness,
)
from xar_autoplayer.native_session import native_session  # noqa: E402
from xar_autoplayer.runtime import (  # noqa: E402
    NativeBridgeLaunchConfig,
    ck3_processes,
    launch,
    stop_tracked,
    utc_now,
)


PURE_NATIVE_MODE = "native-headless"
ONE_GAME_DAY_RAW = 24
ORIGINAL_CHARACTER_ID = 29_829
OWNER_SUBSET_CHARACTER_ID = 36_108
ORIGINAL_ATTACKER_CUNIT_ID = 83_886_341
OWNER_SUBSET_CUNIT_ID = 357
OWNER_SUBSET_NATIVE_CARMY_ID = 344
UNCONTROLLED_ALLY_CUNIT_ID = 33_554_657
UNCONTROLLED_ALLY_OWNER_ID = 28_180
COMBAT_ID = 335_544_325
TARGET_PROVINCE_ID = 2_581
TARGET_CHARACTER_ANCHOR_PROVINCE_ID = 2_543
EXPECTED_SIDE_INDEX = 1
EXPECTED_ACTION_DAY = 15
SEED_SWITCH_MARKER = "XAR_FIXTURE:OWNER_SUBSET_SWITCH|target=36108"
SEED_CLEAR_MARKER = "XAR_FIXTURE:OWNER_SUBSET_GUARD_CLEARED"
SEED_GUARD_VARIABLE = "xar_fixture_owner_subset_switch_consumed"
SEED_POLL_INTERVAL_SECONDS = 0.4
SEED_SETTLE_POLL_INTERVALS = 2
CONTINUE_SAVE_NAME = "autosave.ck3"
MOD_BRIDGE_SOURCE = Path(__file__).resolve().parents[2] / "mod_bridge"
MOD_BRIDGE_TARGET_NAME = "xar-mcp-bridge"
MOD_BRIDGE_OUTER_NAME = "xar_mcp_bridge.mod"
SEED_INBOX_RELATIVE = Path("run/xar_mcp_inbox.txt")
SEED_NOOP_INBOX = (
    "# XAR owner-subset fixture inbox: intentionally no effects.\n"
)
_ROOT_MARKER = ".xar-owner-subset-retreat-fixture.json"
_PROFILE_ROOT_EXCLUDES = frozenset(
    {
        "crashes",
        "dumps",
        "exceptions",
        "logs",
        "mod",
        "mod-content",
        "save games",
        "last_save.ck3",
        "xar-autoplayer-environment.json",
    }
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-state-dir", type=Path, required=True)
    parser.add_argument(
        "--state-dir",
        type=Path,
        help="new disposable root; omitted creates one under the temp dir",
    )
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--battle-save", type=Path, required=True)
    parser.add_argument("--expected-battle-save-sha256", required=True)
    parser.add_argument("--bridge-pipe", required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--readiness-timeout", type=float, default=240.0)
    parser.add_argument("--seed-timeout", type=float, default=30.0)
    parser.add_argument("--postcondition-timeout", type=float, default=10.0)
    parser.add_argument("--retain-state", action="store_true")
    return parser


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _expected_sha256(value: str) -> str:
    normalized = value.strip().upper()
    if len(normalized) != 64 or any(
        character not in "0123456789ABCDEF" for character in normalized
    ):
        raise ValueError("expected battle save SHA-256 must be 64 hex digits")
    return normalized


def _positive_seconds(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    result = float(value)
    if result <= 0:
        raise ValueError(f"{name} must be positive")
    return result


def _copy_source_profile(source_profile: Path, target_profile: Path) -> None:
    for path in source_profile.rglob("*"):
        if path.is_symlink():
            raise AgentError(f"source profile contains a symlink: {path}")

    def ignore(directory: str, names: list[str]) -> set[str]:
        if Path(directory).resolve() == source_profile.resolve():
            return set(names) & _PROFILE_ROOT_EXCLUDES
        return set()

    shutil.copytree(
        source_profile,
        target_profile,
        copy_function=shutil.copy2,
        ignore=ignore,
    )


def _resolve_source_save(
    source_profile: Path, requested: Path, expected_sha256: str
) -> tuple[Path, dict[str, object]]:
    candidate = (
        requested.resolve()
        if requested.is_absolute()
        else (source_profile / requested).resolve()
    )
    if not is_relative_to(candidate, source_profile.resolve()):
        raise AgentError("battle save escapes the source profile")
    if not candidate.is_file():
        raise AgentError(f"battle save is missing: {candidate}")
    actual = _sha256_file(candidate)
    if actual != expected_sha256:
        raise AgentError(
            f"battle save SHA-256 differs: {actual} != {expected_sha256}"
        )
    return candidate, {
        "path": str(candidate),
        "relative_path": candidate.relative_to(source_profile).as_posix(),
        "size": candidate.stat().st_size,
        "sha256": actual,
    }


def _prepare_stage(
    *,
    source_profile: Path,
    target_state: Path,
    game_dir: Path,
    save_source: Path,
    save_name: str,
) -> tuple[Any, dict[str, object]]:
    target = target_state.resolve()
    ensure_state_path_safe(target)
    if target.exists():
        raise AgentError(f"stage state already exists: {target}")
    target.mkdir(parents=True, exist_ok=False)
    _copy_source_profile(source_profile, target / "profile")
    spec = make_spec(target, game_dir)
    manifest = prepare_profile(spec)
    save_dir = spec.profile_dir / "save games"
    save_dir.mkdir(parents=True, exist_ok=True)
    named = save_dir / save_name
    shutil.copy2(save_source, named)
    shutil.copy2(save_source, spec.profile_dir / "last_save.ck3")
    verify_profile(spec)
    return spec, {
        "state_dir": str(target),
        "save_path": str(named),
        "save_name": save_name,
        "save_size": named.stat().st_size,
        "save_sha256": _sha256_file(named),
        "last_save_sha256": _sha256_file(spec.profile_dir / "last_save.ck3"),
        "environment_sha256": manifest.get("environment_sha256"),
    }


def _outer_descriptor(mod_dir: Path) -> str:
    path = mod_dir.resolve().as_posix()
    return (
        '\ufeffversion="0.1.0"\n'
        'tags={\n\t"Utilities"\n}\n'
        'name="XAR Autoplayer MCP Bridge (Development)"\n'
        'supported_version="1.19.0.6"\n'
        f'path="{path}"\n'
    )


def _seed_switch_effect() -> str:
    return (
        f"province:{TARGET_CHARACTER_ANCHOR_PROVINCE_ID} = {{\n"
        "\tprovince_owner = {\n"
        "\t\tsave_temporary_scope_as = xar_fixture_owner_subset_target\n"
        "\t}\n"
        "}\n"
        "if = {\n"
        "\tlimit = {\n"
        "\t\texists = scope:xar_fixture_owner_subset_target\n"
        f"\t\tNOT = {{ global_var:{SEED_GUARD_VARIABLE} = 1 }}\n"
        "\t}\n"
        "\tset_global_variable = {\n"
        f"\t\tname = {SEED_GUARD_VARIABLE}\n"
        "\t\tvalue = 1\n"
        "\t}\n"
        "\tset_player_character = scope:xar_fixture_owner_subset_target\n"
        f'\tdebug_log = "{SEED_SWITCH_MARKER}"\n'
        "}\n"
    )


def _seed_clear_effect() -> str:
    return (
        "if = {\n"
        f"\tlimit = {{ exists = global_var:{SEED_GUARD_VARIABLE} }}\n"
        f"\tremove_global_variable = {SEED_GUARD_VARIABLE}\n"
        f'\tdebug_log = "{SEED_CLEAR_MARKER}"\n'
        "}\n"
    )


def _write_seed_inbox(path: Path, source: str) -> dict[str, object]:
    normalized = source.lstrip("\ufeff")
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        prefix=".xar_mcp_inbox.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(handle, "wb") as temporary:
            temporary.write(b"\xef\xbb\xbf")
            temporary.write(normalized.encode("utf-8"))
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
    raw = path.read_bytes()
    if not raw.startswith(b"\xef\xbb\xbf"):
        raise AgentError("seed inbox atomic replacement lost its UTF-8 BOM")
    return {
        "path": str(path.resolve()),
        "size": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest().upper(),
        "utf8_bom": True,
    }


def _seed_inbox_path(spec: Any) -> Path:
    return spec.profile_dir / SEED_INBOX_RELATIVE


def _debug_log_offset(path: Path) -> int:
    try:
        return path.stat().st_size
    except FileNotFoundError:
        return 0


def _debug_marker_observed(path: Path, marker: str, *, offset: int) -> bool:
    try:
        with path.open("rb") as source:
            source.seek(offset)
            payload = source.read()
    except FileNotFoundError:
        return False
    return marker in payload.decode("utf-8", errors="replace")


def _install_seed_bridge(spec: Any) -> dict[str, object]:
    source = MOD_BRIDGE_SOURCE.resolve()
    if not source.is_dir():
        raise AgentError(f"repository mod_bridge is missing: {source}")
    for path in source.rglob("*"):
        if path.is_symlink():
            raise AgentError(f"repository mod_bridge contains a symlink: {path}")
    target = spec.profile_dir / "mod-content" / MOD_BRIDGE_TARGET_NAME
    target.mkdir(parents=True, exist_ok=False)
    shutil.copy2(source / "descriptor.mod", target / "descriptor.mod")
    for directory in ("common", "gui"):
        shutil.copytree(
            source / directory,
            target / directory,
            copy_function=shutil.copy2,
        )
    outer = spec.profile_dir / "mod" / MOD_BRIDGE_OUTER_NAME
    write_text_atomic(outer, _outer_descriptor(target), encoding="utf-8")
    dlc_load = {
        "enabled_mods": [
            "mod/xar_autoplayer.mod",
            f"mod/{MOD_BRIDGE_OUTER_NAME}",
        ],
        "disabled_dlcs": [],
    }
    write_json_atomic(spec.profile_dir / "dlc_load.json", dlc_load)
    inbox = _write_seed_inbox(_seed_inbox_path(spec), SEED_NOOP_INBOX)
    return {
        "source": str(source),
        "target": str(target),
        "outer_descriptor": str(outer),
        "enabled_mods": dlc_load["enabled_mods"],
        "registered_gui": "gui/xar_mcp_bridge.gui",
        "registered_window": "xar_mcp_bridge_window",
        "poll_interval_seconds": SEED_POLL_INTERVAL_SECONDS,
        "initial_inbox": inbox,
    }


def _played_character_id(snapshot: object) -> int | None:
    if not isinstance(snapshot, dict):
        return None
    played = snapshot.get("played_character")
    value = played.get("character_id") if isinstance(played, dict) else None
    return (
        value
        if isinstance(value, int) and not isinstance(value, bool) and value > 0
        else None
    )


def _validate_owner_subset_frame(frame: object) -> bool:
    if not isinstance(frame, dict):
        return False
    return bool(
        frame.get("status") == "available"
        and frame.get("battle_control_ready") is True
        and frame.get("selected_public_cunit_id") == OWNER_SUBSET_CUNIT_ID
        and frame.get("selected_native_carmy_id")
        == OWNER_SUBSET_NATIVE_CARMY_ID
        and frame.get("selected_owner_character_id")
        == OWNER_SUBSET_CHARACTER_ID
        and frame.get("side_index") == EXPECTED_SIDE_INDEX
        and frame.get("side_scope") == "owner_subset"
        and frame.get("affected_public_cunit_ids_in_stored_order")
        == [OWNER_SUBSET_CUNIT_ID]
        and frame.get(
            "unaffected_same_side_public_cunit_ids_in_stored_order"
        )
        == [UNCONTROLLED_ALLY_CUNIT_ID]
        and retreat_live._battle_combat_id(frame) == COMBAT_ID
    )


def _frame_side_order(frame: object, side_name: str) -> list[int] | None:
    if not isinstance(frame, dict):
        return None
    native = frame.get("battle_control_snapshot")
    side = native.get(side_name) if isinstance(native, dict) else None
    armies = side.get("ordered_armies") if isinstance(side, dict) else None
    if not isinstance(armies, list):
        return None
    result: list[int] = []
    for row in armies:
        value = row.get("public_cunit_id") if isinstance(row, dict) else None
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            return None
        result.append(value)
    return result


def _validate_advance_frame(frame: object) -> bool:
    if not isinstance(frame, dict):
        return False
    native = frame.get("battle_control_snapshot")
    return bool(
        frame.get("status") == "available"
        and frame.get("battle_control_ready") is True
        and frame.get("selected_public_cunit_id")
        == ORIGINAL_ATTACKER_CUNIT_ID
        and frame.get("side_index") == 0
        and frame.get("side_scope") == "full_side"
        and retreat_live._battle_combat_id(frame) == COMBAT_ID
        and isinstance(native, dict)
        and native.get("phase") == "main"
        and native.get("phase_day") == 12
        and _frame_side_order(frame, "attacker")
        == [ORIGINAL_ATTACKER_CUNIT_ID]
        and _frame_side_order(frame, "defender")
        == [OWNER_SUBSET_CUNIT_ID, UNCONTROLLED_ALLY_CUNIT_ID]
    )


def _validate_seed_target_anchor(snapshot: object) -> bool:
    if not isinstance(snapshot, dict):
        return False
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        return False
    matches = [
        war
        for war in wars
        if isinstance(war, dict) and war.get("war_id") == 16_777_290
    ]
    return bool(
        len(matches) == 1
        and matches[0].get("player_side") == "attacker"
        and matches[0].get("primary_opponent_character_id")
        == OWNER_SUBSET_CHARACTER_ID
        and matches[0].get("enemy_primary_default_raise_province_id")
        == TARGET_CHARACTER_ANCHOR_PROVINCE_ID
    )


def _checkpoint_path(spec: Any) -> Path:
    return spec.profile_dir / "save games" / "xar_checkpoint.ck3"


def _checkpoint_identity(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise AgentError(f"checkpoint was not materialized: {path}")
    return {
        "path": str(path.resolve()),
        "name": path.name,
        "size": path.stat().st_size,
        "sha256": _sha256_file(path),
    }


def _advance_to_action_day(
    service: GameplayBridgeService,
    *,
    session_done: threading.Event,
    session_state: dict[str, object],
    readiness_timeout: float,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for day in range(1, EXPECTED_ACTION_DAY + 1):
        before = service.snapshot()
        if _played_character_id(before) != ORIGINAL_CHARACTER_ID:
            raise AgentError("seed advance no longer controls the source player")
        result = service.execute_step(
            "life-advance", expected_revision=int(before["revision"])
        )
        _wait_for_readiness(
            service.driver,
            session_done=session_done,
            session_state=session_state,
            timeout_seconds=readiness_timeout,
            stable_seconds=0.0,
            poll_interval_seconds=0.05,
            cold_start_checkpoint=False,
            allow_terminal=False,
        )
        after = service.snapshot()
        if after.get("date_raw") != before.get("date_raw") + ONE_GAME_DAY_RAW:
            raise AgentError(f"seed day {day} did not advance exactly one day")
        rows.append(
            {
                "day": day,
                "before_date_raw": before.get("date_raw"),
                "after_date_raw": after.get("date_raw"),
                "result": result,
            }
        )
    return rows


def _run_advance_production_session(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    timeout: float,
    readiness_timeout: float,
) -> dict[str, object]:
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    driver: NativeHeadlessGameplayDriver | None = None
    thread: threading.Thread | None = None
    readiness: dict[str, object] | None = None
    advances: list[dict[str, object]] = []
    snapshot: dict[str, object] | None = None
    battle: dict[str, object] | None = None
    save_result: dict[str, object] | None = None
    error: str | None = None
    driver_closed = False

    def supervise() -> None:
        try:
            session_state["report"] = native_session(
                spec,
                timeout_seconds=timeout + 90.0,
                native_bridge=config,
                input_stream=None,
                output_stream=None,
                poll_interval_seconds=0.05,
                cold_start_checkpoint=False,
                stop_event=stop_event,
            )
        except BaseException as caught:
            session_state["error"] = f"{type(caught).__name__}: {caught}"
        finally:
            session_done.set()

    try:
        verify_profile(spec)
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        service = GameplayBridgeService(driver)
        thread = threading.Thread(
            target=supervise,
            name="xar-owner-subset-advance-session",
            daemon=False,
        )
        thread.start()
        readiness = _wait_for_readiness(
            driver,
            session_done=session_done,
            session_state=session_state,
            timeout_seconds=readiness_timeout,
            stable_seconds=0.5,
            poll_interval_seconds=0.05,
            cold_start_checkpoint=False,
            allow_terminal=False,
        )
        advances = _advance_to_action_day(
            service,
            session_done=session_done,
            session_state=session_state,
            readiness_timeout=readiness_timeout,
        )
        snapshot = service.snapshot()
        battle = service.query_battle_control_snapshot_v1(
            ORIGINAL_ATTACKER_CUNIT_ID,
            expected_revision=int(snapshot["revision"]),
        )
        if not _validate_advance_frame(battle):
            raise AgentError("day-15 production battle frame differs")
        current = service.snapshot()
        save_result = service.save_checkpoint(
            expected_revision=int(current["revision"])
        )
        _checkpoint_identity(_checkpoint_path(spec))
    except BaseException as caught:
        error = f"{type(caught).__name__}: {caught}"
    finally:
        stop_event.set()
        if thread is not None:
            thread.join()
        if driver is not None:
            try:
                driver.close()
                driver_closed = True
            except BaseException as caught:
                detail = f"{type(caught).__name__}: {caught}"
                error = detail if error is None else f"{error}; {detail}"
    cleanup = _cleanup_report(
        session_state.get("report"),
        session_error=session_state.get("error"),
        driver_closed=driver_closed,
        elapsed_seconds=0.0,
    )
    return {
        "ok": bool(
            error is None
            and _played_character_id(snapshot) == ORIGINAL_CHARACTER_ID
            and _validate_advance_frame(battle)
            and save_result is not None
            and cleanup.get("ok") is True
        ),
        "production_profile": True,
        "profile_verified": True,
        "readiness": readiness,
        "advances": advances,
        "snapshot": retreat_live._compact_snapshot(
            snapshot, ORIGINAL_ATTACKER_CUNIT_ID
        )
        if snapshot is not None
        else None,
        "battle": battle,
        "save_result": save_result,
        "checkpoint": (
            _checkpoint_identity(_checkpoint_path(spec))
            if _checkpoint_path(spec).is_file()
            else None
        ),
        "session": _compact_session_report(session_state.get("report")),
        "cleanup": cleanup,
        "error": error,
    }


def _fixture_native_session(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    timeout: float,
    stop_event: threading.Event,
) -> dict[str, object]:
    """Own one seed-only CK3 tree while bypassing singleton verification."""
    started_at = utc_now()
    started = time.monotonic()
    handle = None
    shutdown: dict[str, object] | None = None
    exit_reason = "launch_error"
    process_exit_code: int | None = None
    error: str | None = None
    pid: int | None = None
    with exclusive_launch_lock(spec.game_exe):
        with exclusive_state_lock(spec.state_dir, "owner-subset-seed"):
            try:
                handle = launch(
                    spec,
                    native_bridge=config,
                    continue_last_save=True,
                    verify_prepared_profile=False,
                )
                pid = int(handle.process.pid)
                deadline = time.monotonic() + timeout
                while True:
                    process_exit_code = handle.process.poll()
                    if process_exit_code is not None:
                        exit_reason = "process_exit"
                        if process_exit_code != 0:
                            error = f"CK3 exited with code {process_exit_code}"
                        break
                    if stop_event.is_set():
                        exit_reason = "stop"
                        break
                    if time.monotonic() >= deadline:
                        exit_reason = "timeout"
                        error = "seed fixture session timed out"
                        break
                    time.sleep(0.05)
            except BaseException as caught:
                error = f"{type(caught).__name__}: {caught}"
            finally:
                if handle is not None:
                    try:
                        shutdown = stop_tracked(handle, require_running=False)
                    except BaseException as caught:
                        detail = f"{type(caught).__name__}: {caught}"
                        error = detail if error is None else f"{error}; {detail}"
    ok = bool(
        error is None
        and isinstance(shutdown, dict)
        and shutdown.get("ok") is True
    )
    report: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_owner_subset_seed_fixture_session",
        "mode": PURE_NATIVE_MODE,
        "pipe": config.pipe_name,
        "pid": pid,
        "started_at": started_at,
        "finished_at": utc_now(),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "exit_reason": exit_reason,
        "process_exit_code": process_exit_code,
        "shutdown": shutdown,
        "restart_count": 0,
        "restart_shutdowns": [],
        "cold_start_checkpoint": None,
        "ok": ok,
    }
    if not ok:
        raise AgentError(error or "seed fixture session cleanup failed")
    return report


def _run_seed_session(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    timeout: float,
    readiness_timeout: float,
    seed_timeout: float,
    expected_date_raw: int,
) -> dict[str, object]:
    started = time.monotonic()
    driver: NativeHeadlessGameplayDriver | None = None
    thread: threading.Thread | None = None
    driver_closed = False
    error: str | None = None
    readiness: dict[str, object] | None = None
    initial_snapshot: dict[str, object] | None = None
    initial_battle: dict[str, object] | None = None
    switched: dict[str, object] | None = None
    battle: dict[str, object] | None = None
    save_result: dict[str, object] | None = None
    switch_marker_observed = False
    clear_marker_observed = False
    switch_effect: dict[str, object] | None = None
    noop_after_switch: dict[str, object] | None = None
    clear_effect: dict[str, object] | None = None
    final_noop: dict[str, object] | None = None
    switch_poll_frames: list[dict[str, object]] = []
    clear_poll_frames: list[dict[str, object]] = []
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}

    def supervise() -> None:
        try:
            session_state["report"] = _fixture_native_session(
                spec=spec,
                config=config,
                timeout=timeout + 90.0,
                stop_event=stop_event,
            )
        except BaseException as caught:
            session_state["error"] = f"{type(caught).__name__}: {caught}"
        finally:
            session_done.set()

    stop_event = threading.Event()
    try:
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        thread = threading.Thread(
            target=supervise,
            name="xar-owner-subset-seed-session",
            daemon=False,
        )
        thread.start()
        readiness = _wait_for_readiness(
            driver,
            session_done=session_done,
            session_state=session_state,
            timeout_seconds=readiness_timeout,
            stable_seconds=0.5,
            poll_interval_seconds=0.05,
            cold_start_checkpoint=False,
            allow_terminal=True,
        )
        service = GameplayBridgeService(driver)
        initial_snapshot = service.snapshot()
        if _played_character_id(initial_snapshot) != ORIGINAL_CHARACTER_ID:
            raise AgentError("seed session did not start from the source player")
        if initial_snapshot.get("date_raw") != expected_date_raw:
            raise AgentError("seed session did not start on the day-15 date")
        if not _validate_seed_target_anchor(initial_snapshot):
            raise AgentError("seed target province-owner anchor differs")
        initial_battle = service.query_battle_control_snapshot_v1(
            ORIGINAL_ATTACKER_CUNIT_ID,
            expected_revision=int(initial_snapshot["revision"]),
        )
        if not _validate_advance_frame(initial_battle):
            raise AgentError("seed session initial battle frame differs")

        deadline = time.monotonic() + seed_timeout
        debug_log = spec.profile_dir / "logs" / "debug.log"
        switch_log_offset = _debug_log_offset(debug_log)
        switch_effect = _write_seed_inbox(
            _seed_inbox_path(spec),
            _seed_switch_effect(),
        )
        while time.monotonic() < deadline:
            switch_marker_observed = _debug_marker_observed(
                debug_log,
                SEED_SWITCH_MARKER,
                offset=switch_log_offset,
            )
            candidate = service.snapshot()
            if (
                switch_marker_observed
                and _played_character_id(candidate)
                == OWNER_SUBSET_CHARACTER_ID
            ):
                switched = candidate
                break
            if session_done.is_set():
                raise AgentError(
                    str(
                        session_state.get("error")
                        or "seed session ended before player switch"
                    )
                )
            time.sleep(0.05)
        if switched is None:
            raise AgentError(
                "mod_bridge inbox did not produce marker plus player switch"
            )
        if switched.get("date_raw") != expected_date_raw:
            raise AgentError("seed switch advanced the game date")

        noop_after_switch = _write_seed_inbox(
            _seed_inbox_path(spec), SEED_NOOP_INBOX
        )
        poll_driver = DataModGameplayDriver(
            spec.profile_dir,
            request_timeout_seconds=seed_timeout,
            poll_interval_seconds=0.05,
        )
        switch_poll_frames = [
            poll_driver.take_snapshot(),
            poll_driver.take_snapshot(),
        ]
        if (
            len({row.get("request_id") for row in switch_poll_frames}) != 2
            or any(
                row.get("player_id") != OWNER_SUBSET_CHARACTER_ID
                for row in switch_poll_frames
            )
            or switch_poll_frames[0].get("total_days")
            != switch_poll_frames[1].get("total_days")
        ):
            raise AgentError("two post-switch mod_bridge polls were not stable")
        stable_switched = service.snapshot()
        if (
            _played_character_id(stable_switched)
            != OWNER_SUBSET_CHARACTER_ID
            or stable_switched.get("date_raw") != expected_date_raw
        ):
            raise AgentError("player/date changed during two no-op polls")
        switched = stable_switched

        clear_deadline = time.monotonic() + seed_timeout
        clear_log_offset = _debug_log_offset(debug_log)
        clear_effect = _write_seed_inbox(
            _seed_inbox_path(spec), _seed_clear_effect()
        )
        while time.monotonic() < clear_deadline:
            clear_marker_observed = _debug_marker_observed(
                debug_log,
                SEED_CLEAR_MARKER,
                offset=clear_log_offset,
            )
            if clear_marker_observed:
                break
            if session_done.is_set():
                raise AgentError(
                    str(
                        session_state.get("error")
                        or "seed session ended before guard clear"
                    )
                )
            time.sleep(0.05)
        if not clear_marker_observed:
            raise AgentError("mod_bridge did not acknowledge guard removal")
        clear_poll_frames = [
            poll_driver.take_snapshot(),
            poll_driver.take_snapshot(),
        ]
        if (
            len({row.get("request_id") for row in clear_poll_frames}) != 2
            or any(
                row.get("player_id") != OWNER_SUBSET_CHARACTER_ID
                for row in clear_poll_frames
            )
            or clear_poll_frames[0].get("total_days")
            != clear_poll_frames[1].get("total_days")
        ):
            raise AgentError("two post-clear mod_bridge polls were not stable")
        # DataModGameplayDriver restores its own valid no-op after each
        # request.  Publish the fixture's canonical no-op after both proof
        # frames so the saved seed has one byte-stable final inbox identity.
        final_noop = _write_seed_inbox(
            _seed_inbox_path(spec), SEED_NOOP_INBOX
        )
        final_inbox = _seed_inbox_path(spec).read_text(encoding="utf-8-sig")
        if final_inbox != SEED_NOOP_INBOX:
            raise AgentError("seed inbox did not remain at the final no-op")

        switched = service.snapshot()
        if (
            _played_character_id(switched) != OWNER_SUBSET_CHARACTER_ID
            or switched.get("date_raw") != expected_date_raw
        ):
            raise AgentError("seed identity/date changed before battle proof")
        battle = service.query_battle_control_snapshot_v1(
            OWNER_SUBSET_CUNIT_ID,
            expected_revision=int(switched["revision"]),
        )
        if not _validate_owner_subset_frame(battle):
            raise AgentError("seeded mixed-owner battle frame differs")
        current = service.snapshot()
        save_result = service.save_checkpoint(
            expected_revision=int(current["revision"])
        )
        _checkpoint_identity(_checkpoint_path(spec))
    except BaseException as caught:
        error = f"{type(caught).__name__}: {caught}"
    finally:
        try:
            final_noop = _write_seed_inbox(
                _seed_inbox_path(spec), SEED_NOOP_INBOX
            )
        except BaseException as caught:
            detail = f"{type(caught).__name__}: {caught}"
            error = detail if error is None else f"{error}; {detail}"
        stop_event.set()
        if thread is not None:
            thread.join()
        if driver is not None:
            try:
                driver.close()
                driver_closed = True
            except BaseException as caught:
                detail = f"{type(caught).__name__}: {caught}"
                error = detail if error is None else f"{error}; {detail}"
    cleanup = _cleanup_report(
        session_state.get("report"),
        session_error=session_state.get("error"),
        driver_closed=driver_closed,
        elapsed_seconds=0.0,
    )
    return {
        "ok": bool(
            error is None
            and switch_marker_observed
            and clear_marker_observed
            and _played_character_id(switched) == OWNER_SUBSET_CHARACTER_ID
            and isinstance(battle, dict)
            and _validate_owner_subset_frame(battle)
            and save_result is not None
            and cleanup.get("ok") is True
        ),
        "managed_fixture_profile": True,
        "production_profile": False,
        "verification_bypass_reason": (
            "seed-only production plus repository mod_bridge playset; only save "
            "bytes are migrated into fresh verified production-only profiles"
        ),
        "debug_mode": False,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "readiness": readiness,
        "initial_snapshot": retreat_live._compact_snapshot(
            initial_snapshot, ORIGINAL_ATTACKER_CUNIT_ID
        )
        if initial_snapshot is not None
        else None,
        "initial_battle": initial_battle,
        "inbox_protocol": {
            "path": str(_seed_inbox_path(spec).resolve()),
            "poll_interval_seconds": SEED_POLL_INTERVAL_SECONDS,
            "settle_poll_intervals": SEED_SETTLE_POLL_INTERVALS,
            "switch_marker": SEED_SWITCH_MARKER,
            "switch_marker_observed": switch_marker_observed,
            "clear_marker": SEED_CLEAR_MARKER,
            "clear_marker_observed": clear_marker_observed,
            "switch_effect": switch_effect,
            "noop_after_switch": noop_after_switch,
            "clear_effect": clear_effect,
            "final_noop": final_noop,
            "post_switch_frames": switch_poll_frames,
            "post_clear_frames": clear_poll_frames,
        },
        "switched": retreat_live._compact_snapshot(
            switched, OWNER_SUBSET_CUNIT_ID
        )
        if switched is not None
        else None,
        "battle": battle,
        "save_result": save_result,
        "checkpoint": (
            _checkpoint_identity(_checkpoint_path(spec))
            if _checkpoint_path(spec).is_file()
            else None
        ),
        "session": _compact_session_report(session_state.get("report")),
        "driver_closed": driver_closed,
        "ck3_processes_after": ck3_processes(),
        "cleanup": cleanup,
        "cleanup_ok": cleanup.get("ok") is True,
        "error": error,
    }


def _run_canonical_production_session(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    timeout: float,
    readiness_timeout: float,
) -> dict[str, object]:
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    driver: NativeHeadlessGameplayDriver | None = None
    thread: threading.Thread | None = None
    readiness: dict[str, object] | None = None
    snapshot: dict[str, object] | None = None
    battle: dict[str, object] | None = None
    save_result: dict[str, object] | None = None
    error: str | None = None
    driver_closed = False

    def supervise() -> None:
        try:
            session_state["report"] = native_session(
                spec,
                timeout_seconds=timeout + 90.0,
                native_bridge=config,
                input_stream=None,
                output_stream=None,
                poll_interval_seconds=0.05,
                cold_start_checkpoint=False,
                stop_event=stop_event,
            )
        except BaseException as caught:
            session_state["error"] = f"{type(caught).__name__}: {caught}"
        finally:
            session_done.set()

    try:
        verify_profile(spec)
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        service = GameplayBridgeService(driver)
        thread = threading.Thread(
            target=supervise,
            name="xar-owner-subset-canonical-session",
            daemon=False,
        )
        thread.start()
        readiness = _wait_for_readiness(
            driver,
            session_done=session_done,
            session_state=session_state,
            timeout_seconds=readiness_timeout,
            stable_seconds=0.5,
            poll_interval_seconds=0.05,
            cold_start_checkpoint=False,
            allow_terminal=False,
        )
        snapshot = service.snapshot()
        if _played_character_id(snapshot) != OWNER_SUBSET_CHARACTER_ID:
            raise AgentError("production reload did not bind seeded player")
        battle = service.query_battle_control_snapshot_v1(
            OWNER_SUBSET_CUNIT_ID,
            expected_revision=int(snapshot["revision"]),
        )
        if not _validate_owner_subset_frame(battle):
            raise AgentError("production reload lost mixed-owner battle frame")
        current = service.snapshot()
        save_result = service.save_checkpoint(
            expected_revision=int(current["revision"])
        )
        _checkpoint_identity(_checkpoint_path(spec))
    except BaseException as caught:
        error = f"{type(caught).__name__}: {caught}"
    finally:
        stop_event.set()
        if thread is not None:
            thread.join()
        if driver is not None:
            try:
                driver.close()
                driver_closed = True
            except BaseException as caught:
                detail = f"{type(caught).__name__}: {caught}"
                error = detail if error is None else f"{error}; {detail}"
    cleanup = _cleanup_report(
        session_state.get("report"),
        session_error=session_state.get("error"),
        driver_closed=driver_closed,
        elapsed_seconds=0.0,
    )
    return {
        "ok": bool(
            error is None
            and _played_character_id(snapshot) == OWNER_SUBSET_CHARACTER_ID
            and _validate_owner_subset_frame(battle)
            and save_result is not None
            and cleanup.get("ok") is True
        ),
        "production_profile": True,
        "profile_verified": True,
        "readiness": readiness,
        "snapshot": retreat_live._compact_snapshot(
            snapshot, OWNER_SUBSET_CUNIT_ID
        )
        if snapshot is not None
        else None,
        "battle": battle,
        "save_result": save_result,
        "checkpoint": (
            _checkpoint_identity(_checkpoint_path(spec))
            if _checkpoint_path(spec).is_file()
            else None
        ),
        "session": _compact_session_report(session_state.get("report")),
        "cleanup": cleanup,
        "error": error,
    }


def _target_root(requested: Path | None) -> Path:
    if requested is not None:
        return requested.expanduser().resolve()
    return Path(tempfile.gettempdir()).resolve() / (
        "xar-owner-subset-retreat-" + uuid.uuid4().hex
    )


def _cleanup_root(
    root: Path,
    *,
    nonce: str,
    retain: bool,
    all_sessions_clean: bool,
) -> dict[str, object]:
    target = root.resolve()
    if retain:
        return {
            "attempted": False,
            "removed": False,
            "ok": False,
            "path": str(target),
            "reason": "--retain-state prevents cleanup qualification",
        }
    if not all_sessions_clean:
        return {
            "attempted": False,
            "removed": False,
            "ok": False,
            "path": str(target),
            "reason": "a managed session cleanup was not proven",
        }
    marker = target / _ROOT_MARKER
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
        if not (
            payload.get("kind") == "xar_owner_subset_retreat_fixture"
            and payload.get("nonce") == nonce
        ):
            raise AgentError("fixture root marker differs")
        ensure_state_path_safe(target)
        shutil.rmtree(target)
        removed = not target.exists()
        return {
            "attempted": True,
            "removed": removed,
            "ok": removed,
            "path": str(target),
            "reason": None if removed else "fixture root still exists",
        }
    except BaseException as caught:
        return {
            "attempted": True,
            "removed": False,
            "ok": False,
            "path": str(target),
            "reason": f"{type(caught).__name__}: {caught}",
        }


def _run(
    args: argparse.Namespace,
    *,
    action_runner: Callable[
        [Any, NativeBridgeLaunchConfig, float, float, float],
        dict[str, object],
    ]
    | None = None,
) -> tuple[dict[str, object], int]:
    started_at = utc_now()
    started = time.monotonic()
    timeout = _positive_seconds(args.timeout, "timeout")
    readiness_timeout = _positive_seconds(
        args.readiness_timeout, "readiness_timeout"
    )
    seed_timeout = _positive_seconds(args.seed_timeout, "seed_timeout")
    postcondition_timeout = _positive_seconds(
        args.postcondition_timeout, "postcondition_timeout"
    )
    expected_save_sha = _expected_sha256(
        args.expected_battle_save_sha256
    )
    source_state = args.source_state_dir.expanduser().resolve()
    source_profile = source_state / "profile"
    game_dir = args.game_dir.expanduser().resolve()
    root = _target_root(args.state_dir)
    output = args.output.expanduser().resolve()
    if root.exists():
        raise AgentError(f"fixture root already exists: {root}")
    ensure_state_path_safe(root)
    if paths_overlap(source_state, root):
        raise AgentError("source and fixture state roots overlap")
    if is_relative_to(output, root):
        raise AgentError("artifact output must be outside disposable state")
    if output.exists():
        raise AgentError(f"artifact output already exists: {output}")
    source_save, source_identity = _resolve_source_save(
        source_profile, args.battle_save, expected_save_sha
    )
    source_before = _sha256_file(source_save)
    nonce = uuid.uuid4().hex
    root.mkdir(parents=True, exist_ok=False)
    write_json_atomic(
        root / _ROOT_MARKER,
        {
            "kind": "xar_owner_subset_retreat_fixture",
            "nonce": nonce,
            "source_state_dir": str(source_state),
        },
    )

    dll = args.bridge_dll.expanduser().resolve()
    injector = args.bridge_injector.expanduser().resolve()
    config = NativeBridgeLaunchConfig(
        mode=PURE_NATIVE_MODE,
        pipe_name=args.bridge_pipe,
        dll_path=dll,
        injector_path=injector,
    )
    stages: dict[str, object] = {}
    error: str | None = None
    advance: dict[str, object] | None = None
    seed: dict[str, object] | None = None
    canonical: dict[str, object] | None = None
    action: dict[str, object] | None = None
    session_cleanup_flags: list[bool] = []
    try:
        advance_spec, advance_stage = _prepare_stage(
            source_profile=source_profile,
            target_state=root / "advance",
            game_dir=game_dir,
            save_source=source_save,
            # -continuelastsave resolves the persisted autosave slot on this
            # exact build; a root last_save.ck3 pointer alone falls back to
            # the main menu with "Could not load save game [autosave]".
            save_name=CONTINUE_SAVE_NAME,
        )
        stages["advance"] = advance_stage
        advance = _run_advance_production_session(
            spec=advance_spec,
            config=config,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
        )
        session_cleanup_flags.append(
            isinstance(advance.get("cleanup"), dict)
            and advance["cleanup"].get("ok") is True
        )
        if advance.get("ok") is not True:
            raise AgentError(
                str(advance.get("error") or "advance session failed")
            )
        advance_snapshot = advance.get("snapshot")
        expected_action_date_raw = (
            advance_snapshot.get("date_raw")
            if isinstance(advance_snapshot, dict)
            else None
        )
        if not isinstance(expected_action_date_raw, int) or isinstance(
            expected_action_date_raw, bool
        ):
            raise AgentError("advance session lacks the action date")
        advanced_checkpoint = _checkpoint_path(advance_spec)

        seed_spec, seed_stage = _prepare_stage(
            source_profile=source_profile,
            target_state=root / "seed",
            game_dir=game_dir,
            save_source=advanced_checkpoint,
            # launch(..., continue_last_save=True) resolves the copied
            # profile's persisted autosave slot, so every fresh stage must
            # materialize the new bytes under that exact name.
            save_name=CONTINUE_SAVE_NAME,
        )
        seed_stage["fixture_bridge"] = _install_seed_bridge(seed_spec)
        stages["seed"] = seed_stage
        seed = _run_seed_session(
            spec=seed_spec,
            config=config,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            seed_timeout=seed_timeout,
            expected_date_raw=expected_action_date_raw,
        )
        session_cleanup_flags.append(seed.get("cleanup_ok") is True)
        if seed.get("ok") is not True:
            raise AgentError(str(seed.get("error") or "seed session failed"))
        seeded_checkpoint = _checkpoint_path(seed_spec)

        canonical_spec, canonical_stage = _prepare_stage(
            source_profile=source_profile,
            target_state=root / "canonical",
            game_dir=game_dir,
            save_source=seeded_checkpoint,
            save_name=CONTINUE_SAVE_NAME,
        )
        stages["canonical"] = canonical_stage
        canonical = _run_canonical_production_session(
            spec=canonical_spec,
            config=config,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
        )
        session_cleanup_flags.append(
            isinstance(canonical.get("cleanup"), dict)
            and canonical["cleanup"].get("ok") is True
        )
        if canonical.get("ok") is not True:
            raise AgentError(
                str(canonical.get("error") or "canonical session failed")
            )
        canonical_checkpoint = _checkpoint_path(canonical_spec)

        action_spec, action_stage = _prepare_stage(
            source_profile=source_profile,
            target_state=root / "action",
            game_dir=game_dir,
            save_source=canonical_checkpoint,
            save_name=CONTINUE_SAVE_NAME,
        )
        stages["action"] = action_stage
        if action_runner is None:
            action_args = argparse.Namespace(
                state_dir=action_spec.state_dir,
                game_dir=game_dir,
                bridge_pipe=config.pipe_name,
                bridge_dll=dll,
                bridge_injector=injector,
                output=output,
                subject_army_id=OWNER_SUBSET_CUNIT_ID,
                target_province_id=TARGET_PROVINCE_ID,
                expected_scope="owner_subset",
                advance_days_before_preview=0,
                postcondition_timeout=postcondition_timeout,
                timeout=timeout,
                readiness_timeout=readiness_timeout,
                cold_start_checkpoint=False,
            )
            action, _unused_exit = retreat_live._run(action_args)
        else:
            action = action_runner(
                action_spec,
                config,
                timeout,
                readiness_timeout,
                postcondition_timeout,
            )
        action_cleanup = action.get("cleanup")
        session_cleanup_flags.append(
            isinstance(action_cleanup, dict)
            and action_cleanup.get("ok") is True
        )
        if action.get("ok") is not True:
            raise AgentError(str(action.get("error") or "action session failed"))
    except BaseException as caught:
        error = f"{type(caught).__name__}: {caught}"

    source_after = _sha256_file(source_save)
    source_unchanged = source_before == source_after
    all_sessions_clean = bool(
        session_cleanup_flags and all(session_cleanup_flags) and not ck3_processes()
    )
    cleanup = _cleanup_root(
        root,
        nonce=nonce,
        retain=bool(args.retain_state),
        all_sessions_clean=all_sessions_clean,
    )
    if not source_unchanged and error is None:
        error = "source battle save changed"
    if cleanup.get("ok") is not True and error is None:
        error = str(cleanup.get("reason") or "fixture cleanup failed")
    owner_ready = bool(
        isinstance(action, dict)
        and isinstance(action.get("readiness_gates"), dict)
        and action["readiness_gates"].get(
            "owner_subset_postcondition_live_ready"
        )
        is True
    )
    ok = bool(
        error is None
        and advance is not None
        and advance.get("ok") is True
        and seed is not None
        and seed.get("ok") is True
        and canonical is not None
        and canonical.get("ok") is True
        and action is not None
        and action.get("ok") is True
        and owner_ready
        and source_unchanged
        and cleanup.get("ok") is True
    )
    payload: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_owner_subset_active_retreat_live_acceptance",
        "started_at": started_at,
        "finished_at": utc_now(),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "ok": ok,
        "exact_fixture": {
            "original_character_id": ORIGINAL_CHARACTER_ID,
            "played_character_id": OWNER_SUBSET_CHARACTER_ID,
            "combat_id": COMBAT_ID,
            "subject_public_cunit_id": OWNER_SUBSET_CUNIT_ID,
            "subject_native_carmy_id": OWNER_SUBSET_NATIVE_CARMY_ID,
            "side_index": EXPECTED_SIDE_INDEX,
            "side_scope": "owner_subset",
            "affected_public_cunit_ids_in_stored_order": [
                OWNER_SUBSET_CUNIT_ID
            ],
            "unaffected_same_side_public_cunit_ids_in_stored_order": [
                UNCONTROLLED_ALLY_CUNIT_ID
            ],
            "unaffected_owner_character_id": UNCONTROLLED_ALLY_OWNER_ID,
            "opposite_public_cunit_ids_in_stored_order": [
                ORIGINAL_ATTACKER_CUNIT_ID
            ],
            "target_province_id": TARGET_PROVINCE_ID,
            "action_day": EXPECTED_ACTION_DAY,
        },
        "identity": {
            "bridge_pipe": config.pipe_name,
            "bridge_dll": str(dll),
            "bridge_dll_sha256": _sha256_file(dll),
            "bridge_injector": str(injector),
            "bridge_injector_sha256": _sha256_file(injector),
        },
        "source_save": source_identity
        | {
            "before_sha256": source_before,
            "after_sha256": source_after,
            "unchanged": source_unchanged,
        },
        "stages": stages,
        "advance_production": advance,
        "seed": seed,
        "canonical_production_reload": canonical,
        "action_production_reload": action,
        "readiness_gates": {
            "advance_day15_production_ready": bool(
                isinstance(advance, dict) and advance.get("ok") is True
            ),
            "seed_mod_bridge_switch_marker_observed": bool(
                isinstance(seed, dict)
                and isinstance(seed.get("inbox_protocol"), dict)
                and seed["inbox_protocol"].get("switch_marker_observed")
                is True
            ),
            "seed_mod_bridge_guard_clear_observed": bool(
                isinstance(seed, dict)
                and isinstance(seed.get("inbox_protocol"), dict)
                and seed["inbox_protocol"].get("clear_marker_observed")
                is True
            ),
            "seed_mod_bridge_two_poll_cycles_ready": bool(
                isinstance(seed, dict)
                and isinstance(seed.get("inbox_protocol"), dict)
                and len(seed["inbox_protocol"].get("post_switch_frames", []))
                == SEED_SETTLE_POLL_INTERVALS
                and len(seed["inbox_protocol"].get("post_clear_frames", []))
                == SEED_SETTLE_POLL_INTERVALS
            ),
            "seed_same_date_player_switch_ready": bool(
                isinstance(seed, dict) and seed.get("ok") is True
            ),
            "canonical_production_reload_ready": bool(
                isinstance(canonical, dict) and canonical.get("ok") is True
            ),
            "owner_subset_postcondition_live_ready": owner_ready,
            "source_save_unchanged": source_unchanged,
            "managed_cleanup_ready": bool(
                all_sessions_clean and cleanup.get("ok") is True
            ),
        },
        "state_cleanup": cleanup,
        "error": error,
    }
    return payload, 0 if ok else 1


def main() -> int:
    args = _parser().parse_args()
    payload, exit_code = _run(args)
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": payload.get("ok"),
                "output": str(output),
                "artifact_sha256": _sha256_file(output),
                "readiness_gates": payload.get("readiness_gates"),
                "state_cleanup": payload.get("state_cleanup"),
                "error": payload.get("error"),
            },
            ensure_ascii=False,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
