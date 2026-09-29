"""One fixed read-only stationary route-contact query under production ownership.

This module deliberately owns a normal ``native_session`` instead of using a
research acceptance harness.  It admits one exact paused read-only query and
then stops the managed CK3 process.  It has no planner or action dispatch.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
import threading
import time

from .bridge.native_driver import (
    NativeHeadlessGameplayDriver,
    _army_by_id,
    _army_in_combat_or_retreat,
    _army_is_known_stationary,
    _canonical_remaining_route,
    _route_contact_hostile_ids,
)
from .bridge.service import GameplayBridgeService
from .bridge.succession_transition_contract import (
    ORDINARY_CAMPAIGN_SUCCESSION,
    bind_succession_lifecycle_from_environment_v1,
)
from .bridge.war_contract import query_route_contact_horizon_step
from .environment import EnvironmentSpec, ensure_state_path_safe
from .errors import AgentError
from .native_auto_run import (
    READINESS_POLL_SECONDS,
    READINESS_STABLE_SECONDS,
    SESSION_TIMEOUT_GRACE_SECONDS,
    _cleanup_report,
    _public_binding,
    _wait_for_readiness,
)
from .native_session import native_session, validate_cold_start_checkpoint_for_pipe
from .runtime import (
    NativeBridgeLaunchConfig,
    native_bridge_launch_config_from_environment,
    utc_now,
    validate_native_bridge_launch_config,
)


ARMY_ID = 83886367
TARGET_PROVINCE_ID = 2610
HOSTILE_ARMY_IDS = (50331920, 83886484)
QUERY_STEP = query_route_contact_horizon_step(
    ARMY_ID, TARGET_PROVINCE_ID, list(HOSTILE_ARMY_IDS)
)
CHECKPOINT_SHA256 = "92A06F540E98A767D3E1DB95A6F3870674E0A7F084C2A14BD2D04D354E53DAF6"
RAW_SOURCE_DRIVER_SHA256 = "2F0673EC4D0AFA2A77DE59FE9405EC032CF00F79D9484BBD3DC4361EC1311722"
DLL_SHA256 = "A8EAC0CD5BEEDF90778C76C14679629A96EDD4F7E7B398EB035B865F776786E9"
INJECTOR_SHA256 = "8C8277EC27602C35A3868E17DD60A954151E13E38DCA1456B6F3B34D60EB3544"
CHILD_PENDING_SIDECAR_SHA256 = "798F16F572FB83399CC9AB7ABD16561E87C47CEF7109CF23D255DAE660A8D8A7"
SOURCE_HISTORICAL_PREPARED_STATE_DIR = r"Z:\nw-family-h3937-12turn-20260929\state"
EXPECTED_EPISODE_RUN_ID = "native-29829-2bc2d599f7f9"
EXPECTED_DATE_RAW = 53219928
EXPECTED_HISTORY_INDEX = 3937
# The selected source bytes are receiver verified. They do not establish a fresh
# H3937 hostile scope or a new official prepared pair for this runner checkout.
RECEIVER_ASSETS_AND_SCOPE_VERIFIED = False
ROUND_PATTERN = re.compile(r"R[1-9][0-9]*")


def _read_rebind_receipt(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"cannot read ordinary rebind receipt: {error}") from error
    if not isinstance(value, dict):
        raise AgentError("ordinary rebind receipt is not an object")
    return value


def _same_absolute_path(value: object, expected: Path) -> bool:
    return bool(
        isinstance(value, str)
        and value
        and Path(value).is_absolute()
        and str(Path(value).resolve()).casefold()
        == str(expected.resolve()).casefold()
    )


def _exact_prepared_rebind(
    receipt: object, *, prepared_driver_sha256: str, pipe_name: str,
    state_dir: Path, profile_dir: Path, environment_sha256: str,
) -> bool:
    if not isinstance(receipt, dict):
        return False
    driver = receipt.get("driver_state")
    save = receipt.get("save")
    expectations = receipt.get("no_launch_preflight_expectations")
    post = receipt.get("post_rebind_validation")
    environment = receipt.get("environment")
    safety = receipt.get("safety_contract")
    inventory = receipt.get("process_inventory")
    source_save = save.get("source") if isinstance(save, dict) else None
    target_save = save.get("target") if isinstance(save, dict) else None
    post_checkpoint = post.get("checkpoint") if isinstance(post, dict) else None
    save_path = profile_dir / "save games" / "xar_checkpoint.ck3"
    driver_path = state_dir / "native-session" / "driver-state.json"
    return bool(
        receipt.get("schema") == "xar.ck3.ordinary-seed-rebind/v1"
        and receipt.get("ok") is True
        and receipt.get("status") == "rebound"
        and receipt.get("ck3_launch_attempted") is False
        and receipt.get("desktop_interaction") is False
        and isinstance(inventory, dict)
        and inventory.get("processes") == []
        and isinstance(safety, dict)
        and safety.get("zero_running_ck3_processes") is True
        and safety.get("target_profile_verified") is True
        and safety.get("canonical_paths_only") is True
        and receipt.get("pipe_name") == pipe_name
        and _same_absolute_path(receipt.get("state_dir"), state_dir)
        and not _same_absolute_path(
            receipt.get("state_dir"), Path(SOURCE_HISTORICAL_PREPARED_STATE_DIR)
        )
        and _same_absolute_path(receipt.get("profile_dir"), profile_dir)
        and isinstance(environment_sha256, str)
        and re.fullmatch(r"[0-9a-fA-F]{64}", environment_sha256) is not None
        and isinstance(environment, dict)
        and str(environment.get("target_sha256", "")).casefold()
        == environment_sha256.casefold()
        and isinstance(driver, dict)
        and _same_absolute_path(driver.get("path"), driver_path)
        and str(driver.get("source_sha256", "")).casefold()
        == RAW_SOURCE_DRIVER_SHA256.casefold()
        and str(driver.get("target_sha256", "")).casefold()
        == prepared_driver_sha256.casefold()
        and isinstance(save, dict)
        and save.get("bytes_unchanged") is True
        and isinstance(source_save, dict)
        and isinstance(target_save, dict)
        and _same_absolute_path(source_save.get("path"), save_path)
        and _same_absolute_path(target_save.get("path"), save_path)
        and str(source_save.get("sha256", "")).casefold()
        == CHECKPOINT_SHA256.casefold()
        and str(target_save.get("sha256", "")).casefold()
        == CHECKPOINT_SHA256.casefold()
        and isinstance(expectations, dict)
        and expectations.get("pipe_name") == pipe_name
        and expectations.get("expected_character_id") == 29829
        and expectations.get("expected_episode_run_id") == EXPECTED_EPISODE_RUN_ID
        and str(expectations.get("expected_checkpoint_sha256", "")).casefold()
        == CHECKPOINT_SHA256.casefold()
        and str(expectations.get("expected_driver_state_sha256", "")).casefold()
        == prepared_driver_sha256.casefold()
        and expectations.get("xar_enabled") == "xar_off"
        and expectations.get("succession_lifecycle")
        == "ordinary_campaign_succession"
        and expectations.get("ordinary_campaign_no_pact") is True
        and isinstance(post, dict)
        and post.get("native_driver_consumer") == "passed"
        and post.get("cold_checkpoint_validator") == "passed"
        and isinstance(post_checkpoint, dict)
        and _same_absolute_path(post_checkpoint.get("path"), save_path)
        and post_checkpoint.get("history_index") == EXPECTED_HISTORY_INDEX
        and str(post_checkpoint.get("sha256", "")).casefold()
        == CHECKPOINT_SHA256.casefold()
    )


def _exact_h3937_paused_subject(snapshot: object) -> bool:
    if not isinstance(snapshot, dict):
        return False
    wars = snapshot.get("active_wars")
    armies = snapshot.get("player_armies")
    subject = _army_by_id(snapshot, ARMY_ID)
    played = snapshot.get("played_character")
    war = wars[0] if isinstance(wars, list) and len(wars) == 1 else None
    enemies = war.get("enemy_armies") if isinstance(war, dict) else None
    return bool(
        snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
        and snapshot.get("date_raw") == EXPECTED_DATE_RAW
        and snapshot.get("episode_run_id") == EXPECTED_EPISODE_RUN_ID
        and isinstance(played, dict)
        and played.get("character_id") == 29829
        and snapshot.get("episode_character_id") == 29829
        and snapshot.get("route_contact_horizon_supported") is True
        and isinstance(war, dict)
        and war.get("war_id") == 16777231
        and isinstance(armies, list)
        and sorted(
            army.get("army_id")
            for army in armies
            if isinstance(army, dict) and army.get("controllable") is True
        ) == [ARMY_ID]
        and isinstance(enemies, list)
        and len(enemies) == 2
        and sorted(
            enemy.get("army_id")
            for enemy in enemies if isinstance(enemy, dict)
        ) == list(HOSTILE_ARMY_IDS)
        and all(
            isinstance(enemy, dict)
            and enemy.get("current_province_id") == 2629
            and "move_target_province_id" in enemy
            and enemy.get("move_target_province_id") is None
            and enemy.get("route_province_ids") == []
            and enemy.get("retreating") is False
            and enemy.get("in_combat") is False
            and enemy.get("army_state") in {"regular", "sieging"}
            for enemy in enemies
        )
        and "active_event" in snapshot
        and snapshot.get("active_event") is None
        and "pending_character_interaction" in snapshot
        and snapshot.get("pending_character_interaction") is None
        and _route_contact_hostile_ids(snapshot) == HOSTILE_ARMY_IDS
        and isinstance(subject, dict)
        and subject.get("controllable") is True
        and subject.get("current_province_id") == TARGET_PROVINCE_ID
        and "move_target_province_id" in subject
        and subject.get("move_target_province_id") is None
        and _canonical_remaining_route(subject) == []
        and _army_is_known_stationary(subject)
        and not _army_in_combat_or_retreat(subject)
    )


def _exact_one_appended_query(before: object, after: object, result: object) -> bool:
    before_history = _snapshot_history(before)
    after_history = _snapshot_history(after)
    if not isinstance(before_history, list) or not isinstance(after_history, list):
        return False
    row = after_history[-1] if after_history else None
    return bool(
        len(after_history) == len(before_history) + 1
        and after_history[:-1] == before_history
        and isinstance(row, dict)
        and row.get("command") == QUERY_STEP
        and row.get("ok") is True
        and row.get("result") == result
    )


def _bound_route_result(before: object, result: object) -> bool:
    if not isinstance(before, dict) or not isinstance(result, dict):
        return False
    diagnostics = before.get("diagnostics")
    generation = (
        diagnostics.get("connection_generation")
        if isinstance(diagnostics, dict) else None
    )
    horizon = result.get("route_contact_horizon")
    subject_route = (
        horizon.get("subject_route") if isinstance(horizon, dict) else None
    )
    return bool(
        isinstance(before.get("snapshot_id"), str)
        and bool(before.get("snapshot_id"))
        and type(before.get("revision")) is int
        and before.get("revision") >= 0
        and type(before.get("native_revision")) is int
        and before.get("native_revision") > 0
        and type(generation) is int
        and generation > 0
        and result.get("step") == QUERY_STEP
        and result.get("accepted") is True
        and result.get("status") == "available"
        and type(result.get("query_sequence")) is int
        and result.get("query_sequence") > 0
        and result.get("snapshot_revision") == before.get("native_revision")
        and result.get("queried_snapshot_id") == before.get("snapshot_id")
        and result.get("queried_revision") == before.get("revision")
        and result.get("queried_native_revision")
        == before.get("native_revision")
        and result.get("queried_connection_generation") == generation
        and result.get("queried_episode_run_id") == EXPECTED_EPISODE_RUN_ID
        and isinstance(horizon, dict)
        and horizon.get("status") == "available"
        and horizon.get("date_raw") == EXPECTED_DATE_RAW
        and horizon.get("horizon_start_date_raw") == EXPECTED_DATE_RAW
        and horizon.get("horizon_end_date_raw") == EXPECTED_DATE_RAW + 24
        and type(horizon.get("one_day_contact_free")) is bool
        and horizon.get("snapshot_revision") == before.get("native_revision")
        and horizon.get("subject_army_id") == ARMY_ID
        and horizon.get("target_province_id") == TARGET_PROVINCE_ID
        and horizon.get("hostile_army_ids") == list(HOSTILE_ARMY_IDS)
        and isinstance(subject_route, dict)
        and subject_route.get("army_id") == ARMY_ID
        and subject_route.get("current_province_id") == TARGET_PROVINCE_ID
        and subject_route.get("route_province_ids") == []
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_driver_state(path: Path) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AgentError(f"cannot read native driver state: {error}") from error
    if not isinstance(value, dict):
        raise AgentError("native driver state is not an object")
    return value


def _bind_exact_h3937_ordinary_lifecycle(
    spec: EnvironmentSpec,
    checkpoint: dict[str, object],
    driver_state: dict[str, object],
) -> dict[str, object]:
    """Bind the query driver to the prepared ordinary profile before launch."""
    try:
        manifest = json.loads(spec.manifest_path.read_text(encoding="utf-8-sig"))
        binding = bind_succession_lifecycle_from_environment_v1(
            manifest,
            lifecycle=ORDINARY_CAMPAIGN_SUCCESSION,
            ordinary_campaign_no_pact=True,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise AgentError(
            f"H3937 stationary lifecycle profile is not runnable: {error}"
        ) from error
    anchor = driver_state.get("last_checkpoint")
    if (
        checkpoint.get("succession_lifecycle") != binding
        or driver_state.get("succession_lifecycle") != binding
        or not isinstance(anchor, dict)
        or anchor.get("succession_lifecycle") != binding
    ):
        raise AgentError(
            "H3937 stationary lifecycle differs from the prepared ordinary profile"
        )
    return binding


def _command_history(value: object) -> list[object] | None:
    history = value.get("command_history") if isinstance(value, dict) else None
    if not isinstance(history, list):
        return None
    return copy.deepcopy(history)


def _snapshot_history(value: object) -> list[object] | None:
    history = (
        value.get("native_command_history") if isinstance(value, dict) else None
    )
    if not isinstance(history, list):
        return None
    return copy.deepcopy(history)


def _cold_restore_bookkeeping(
    before_driver_state: dict[str, object],
    query_before: object,
    checkpoint: dict[str, object],
) -> dict[str, object]:
    before_history = _command_history(before_driver_state)
    query_history = _snapshot_history(query_before)
    checkpoint_history_index = checkpoint.get("history_index")
    checkpoint_prefix = (
        before_history[:checkpoint_history_index]
        if before_history is not None
        and isinstance(checkpoint_history_index, int)
        and not isinstance(checkpoint_history_index, bool)
        and checkpoint_history_index >= 0
        and len(before_history) >= checkpoint_history_index
        else None
    )
    restore_entry = (
        query_history[-1]
        if checkpoint_prefix is not None
        and query_history is not None
        and len(query_history) == checkpoint_history_index + 1
        and query_history[:-1] == checkpoint_prefix
        else None
    )
    result = restore_entry.get("result") if isinstance(restore_entry, dict) else None
    restored_checkpoint = (
        result.get("checkpoint") if isinstance(result, dict) else None
    )
    lifecycle = result.get("lifecycle") if isinstance(result, dict) else None
    prior_pid = before_driver_state.get("bridge_pid")
    current_pid = lifecycle.get("pid") if isinstance(lifecycle, dict) else None
    expected_index = (
        checkpoint_history_index + 1
        if isinstance(checkpoint_history_index, int)
        and not isinstance(checkpoint_history_index, bool)
        and checkpoint_history_index >= 0
        else None
    )
    checkpoint_date = checkpoint.get("saved_date_raw")
    checkpoint_sha = checkpoint.get("sha256")
    exact = bool(
        isinstance(restore_entry, dict)
        and restore_entry.get("index") == expected_index
        and restore_entry.get("command") == "restore-checkpoint"
        and restore_entry.get("ok") is True
        and isinstance(result, dict)
        and result.get("step") == "restore-checkpoint"
        and result.get("accepted") is True
        and result.get("status") == "restored"
        and result.get("backend_id") == "native-headless"
        and result.get("source") == "native-session-cold-start"
        and result.get("restored_date_raw") == checkpoint_date
        and result.get("map_ready") is True
        and isinstance(restored_checkpoint, dict)
        and restored_checkpoint.get("sha256") == checkpoint_sha
        and restored_checkpoint.get("date_raw") == checkpoint_date
        and restored_checkpoint.get("history_index") == checkpoint_history_index
        and isinstance(lifecycle, dict)
        and lifecycle.get("previous_pid") == prior_pid
        and isinstance(current_pid, int)
        and not isinstance(current_pid, bool)
        and current_pid > 0
    )
    return {
        "exact": exact,
        "history_before_count": (
            len(before_history) if before_history is not None else None
        ),
        "history_at_query_count": (
            len(query_history) if query_history is not None else None
        ),
        "truncated_tail_count": (
            len(before_history) - checkpoint_history_index
            if before_history is not None
            and isinstance(checkpoint_history_index, int)
            and not isinstance(checkpoint_history_index, bool)
            and 0 <= checkpoint_history_index <= len(before_history)
            else None
        ),
        "restore_entry": copy.deepcopy(restore_entry),
    }


def _same_frame(left: object, right: object) -> bool:
    left_diagnostics = left.get("diagnostics") if isinstance(left, dict) else None
    right_diagnostics = right.get("diagnostics") if isinstance(right, dict) else None
    left_generation = (
        left_diagnostics.get("connection_generation")
        if isinstance(left_diagnostics, dict)
        else left.get("connection_generation") if isinstance(left, dict) else None
    )
    right_generation = (
        right_diagnostics.get("connection_generation")
        if isinstance(right_diagnostics, dict)
        else right.get("connection_generation") if isinstance(right, dict) else None
    )
    return bool(
        isinstance(left, dict)
        and isinstance(right, dict)
        and isinstance(left.get("snapshot_id"), str)
        and bool(left.get("snapshot_id"))
        and type(left.get("revision")) is int
        and left.get("revision") >= 0
        and type(left.get("native_revision")) is int
        and left.get("native_revision") > 0
        and type(left.get("date_raw")) is int
        and left.get("date_raw") == EXPECTED_DATE_RAW
        and left.get("episode_run_id") == EXPECTED_EPISODE_RUN_ID
        and all(
            left.get(key) == right.get(key)
            for key in (
                "snapshot_id",
                "revision",
                "native_revision",
                "date_raw",
                "paused",
                "map_ready",
                "episode_run_id",
            )
        )
        and isinstance(left_generation, int)
        and not isinstance(left_generation, bool)
        and left_generation > 0
        and left_generation == right_generation
    )


def _query_history_unchanged(before: object, after: object) -> bool:
    before_history = _snapshot_history(before)
    return bool(
        before_history is not None and _snapshot_history(after) == before_history
    )


def _guarded_subject_unchanged(before: object, after: object) -> bool:
    if not isinstance(before, dict) or not isinstance(after, dict):
        return False
    return all(
        key in before and key in after and before[key] == after[key]
        for key in (
            "played_character",
            "episode_character_id",
            "active_wars",
            "player_armies",
            "active_event",
            "pending_character_interaction",
            "route_contact_horizon_supported",
        )
    )


def _positive_seconds(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise AgentError(f"{name} must be positive")
    return float(value)


def query_h3937_stationary_route_contact_once(
    spec: EnvironmentSpec,
    *,
    timeout_seconds: float,
    readiness_timeout_seconds: float,
    ownership_round_id: str,
    cold_start_checkpoint: bool,
    native_bridge: NativeBridgeLaunchConfig | None = None,
    readiness_stable_seconds: float = READINESS_STABLE_SECONDS,
    poll_interval_seconds: float = READINESS_POLL_SECONDS,
) -> dict[str, object]:
    """Launch one managed session, issue one private query, and recycle CK3."""

    if RECEIVER_ASSETS_AND_SCOPE_VERIFIED is not True:
        raise AgentError("H3937 metadata-only candidate: matched bytes and paused hostile scope are not receiver-qualified; no launch")
    timeout = _positive_seconds(timeout_seconds, "timeout_seconds")
    readiness_timeout = _positive_seconds(
        readiness_timeout_seconds, "readiness_timeout_seconds"
    )
    stable_seconds = float(readiness_stable_seconds)
    poll_seconds = _positive_seconds(poll_interval_seconds, "poll_interval_seconds")
    if stable_seconds < 0:
        raise AgentError("readiness_stable_seconds must be non-negative")
    if ROUND_PATTERN.fullmatch(ownership_round_id) is None:
        raise AgentError("H3937 stationary route-contact query requires a monotonic R<number> round ID")
    if cold_start_checkpoint is not True:
        raise AgentError("H3937 stationary route-contact query requires an exact cold-start checkpoint")

    config = (
        native_bridge_launch_config_from_environment()
        if native_bridge is None
        else validate_native_bridge_launch_config(native_bridge)
    )
    if config is None or config.mode != "native-headless":
        selected = "disabled" if config is None else config.mode
        raise AgentError(
            "H3937 stationary route-contact query requires --bridge-mode native-headless; "
            f"selected mode is {selected!r}"
        )

    ensure_state_path_safe(spec.state_dir)
    checkpoint = validate_cold_start_checkpoint_for_pipe(spec, config.pipe_name)
    save_path = spec.profile_dir / "save games" / "xar_checkpoint.ck3"
    driver_state_path = spec.state_dir / "native-session" / "driver-state.json"
    child_sidecar_path = spec.state_dir / "player-child-matrilineal-formal-v1.json"
    before_driver_state = _read_driver_state(driver_state_path)
    rebind_receipt_path = spec.state_dir / "ordinary-seed-rebind-v1.json"
    rebind_receipt = _read_rebind_receipt(rebind_receipt_path)
    lifecycle = checkpoint.get("succession_lifecycle")
    driver_checkpoint = before_driver_state.get("last_checkpoint")
    environment_sha256 = (
        lifecycle.get("environment_sha256")
        if isinstance(lifecycle, dict) else None
    )
    before_files = {
        "checkpoint": {"path": str(save_path.resolve()), "sha256": _sha256(save_path)},
        "driver_state": {
            "path": str(driver_state_path.resolve()),
            "sha256": _sha256(driver_state_path),
        },
        "child_pending_sidecar": {
            "path": str(child_sidecar_path.resolve()),
            "sha256": _sha256(child_sidecar_path),
        },
        "bridge_dll": {
            "path": str(config.dll_path.resolve()),
            "sha256": _sha256(config.dll_path),
        },
        "bridge_injector": {
            "path": str(config.injector_path.resolve()),
            "sha256": _sha256(config.injector_path),
        },
    }
    if (
        before_files["checkpoint"]["sha256"].casefold()
        != CHECKPOINT_SHA256.casefold()
        or before_files["child_pending_sidecar"]["sha256"].casefold()
        != CHILD_PENDING_SIDECAR_SHA256.casefold()
        or before_files["bridge_dll"]["sha256"].casefold()
        != DLL_SHA256.casefold()
        or before_files["bridge_injector"]["sha256"].casefold()
        != INJECTOR_SHA256.casefold()
        or not _exact_prepared_rebind(
            rebind_receipt,
            prepared_driver_sha256=before_files["driver_state"]["sha256"],
            pipe_name=config.pipe_name,
            state_dir=spec.state_dir,
            profile_dir=spec.profile_dir,
            environment_sha256=environment_sha256 or "",
        )
        or checkpoint.get("saved_date_raw") != EXPECTED_DATE_RAW
        or checkpoint.get("history_index") != EXPECTED_HISTORY_INDEX
        or before_driver_state.get("episode_run_id") != EXPECTED_EPISODE_RUN_ID
        or before_driver_state.get("episode_character_id") != 29829
        or not isinstance(driver_checkpoint, dict)
        or driver_checkpoint.get("episode_run_id") != EXPECTED_EPISODE_RUN_ID
        or driver_checkpoint.get("episode_character_id") != 29829
        or driver_checkpoint.get("history_index") != EXPECTED_HISTORY_INDEX
        or str(driver_checkpoint.get("sha256", "")).casefold()
        != CHECKPOINT_SHA256.casefold()
        or not isinstance(lifecycle, dict)
        or lifecycle.get("xar_enabled") != "xar_off"
        or lifecycle.get("lifecycle") != "ordinary_campaign_succession"
        or lifecycle.get("pact_contract")
        != "absent_by_fresh_campaign_xar_off_contract"
    ):
        raise AgentError("H3937 source pair identity differs; launch refused")
    lifecycle = _bind_exact_h3937_ordinary_lifecycle(
        spec, checkpoint, before_driver_state
    )
    started_at = utc_now()
    started = time.monotonic()
    deadline = started + timeout
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    driver: NativeHeadlessGameplayDriver | None = None
    session_thread: threading.Thread | None = None
    driver_closed = False
    readiness: dict[str, object] | None = None
    query_before: dict[str, object] | None = None
    query_after: dict[str, object] | None = None
    query_envelope: dict[str, object] | None = None
    primary_error: str | None = None

    def supervise() -> None:
        try:
            session_state["report"] = native_session(
                spec,
                timeout_seconds=timeout + SESSION_TIMEOUT_GRACE_SECONDS,
                native_bridge=config,
                input_stream=None,
                output_stream=None,
                poll_interval_seconds=poll_seconds,
                cold_start_checkpoint=True,
                stop_event=stop_event,
                prepared_xar_enabled="xar_off",
            )
        except BaseException as error:  # returned to the owning thread
            session_state["error"] = f"{type(error).__name__}: {error}"
        finally:
            session_done.set()

    try:
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
            succession_lifecycle_binding=lifecycle,
        )
        service = GameplayBridgeService(driver)
        session_thread = threading.Thread(
            target=supervise,
            name="xar-h3937-stationary-route-contact-query-session",
            daemon=False,
        )
        session_thread.start()
        readiness = _wait_for_readiness(
            driver,
            session_done=session_done,
            session_state=session_state,
            timeout_seconds=min(
                readiness_timeout, max(0.001, deadline - time.monotonic())
            ),
            stable_seconds=stable_seconds,
            poll_interval_seconds=poll_seconds,
            cold_start_checkpoint=True,
            allow_terminal=False,
            require_post_ready_pump=True,
        )
        if time.monotonic() >= deadline:
            raise AgentError("H3937 stationary route-contact query timeout expired before query")
        query_before = service.snapshot()
        revision = query_before.get("revision")
        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 0
            or query_before.get("paused") is not True
            or query_before.get("map_ready") is not True
            or not _exact_h3937_paused_subject(query_before)
        ):
            raise AgentError("H3937 target 2610 stationary same-frame gate failed")
        query_envelope = service.execute_step(
            QUERY_STEP, expected_revision=revision
        )
        query_after = service.snapshot()
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        stop_started = time.monotonic()
        stop_event.set()
        if session_thread is not None:
            session_thread.join()
        stop_elapsed = round(max(0.0, time.monotonic() - stop_started), 3)
        if driver is not None:
            try:
                driver.close()
                driver_closed = True
            except BaseException as error:
                detail = f"{type(error).__name__}: {error}"
                primary_error = (
                    detail
                    if primary_error is None
                    else f"{primary_error}; driver close failed: {detail}"
                )

    cleanup = _cleanup_report(
        session_state.get("report"),
        session_error=session_state.get("error"),
        driver_closed=driver_closed,
        elapsed_seconds=stop_elapsed,
    )
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(
            session_state.get("error")
            or cleanup.get("reason")
            or "managed native-session cleanup was not proven"
        )

    after_files: dict[str, object] = {}
    after_driver_state: dict[str, object] | None = None
    try:
        after_driver_state = _read_driver_state(driver_state_path)
        after_files = {
            "checkpoint": {
                "path": str(save_path.resolve()),
                "sha256": _sha256(save_path),
            },
            "driver_state": {
                "path": str(driver_state_path.resolve()),
                "sha256": _sha256(driver_state_path),
            },
            "child_pending_sidecar": {
                "path": str(child_sidecar_path.resolve()),
                "sha256": _sha256(child_sidecar_path),
            },
            "bridge_dll": {
                "path": str(config.dll_path.resolve()),
                "sha256": _sha256(config.dll_path),
            },
            "bridge_injector": {
                "path": str(config.injector_path.resolve()),
                "sha256": _sha256(config.injector_path),
            },
        }
    except (OSError, AgentError) as error:
        if primary_error is None:
            primary_error = f"{type(error).__name__}: {error}"

    horizon = (
        query_envelope.get("route_contact_horizon")
        if isinstance(query_envelope, dict)
        else None
    )
    before_date = query_before.get("date_raw") if isinstance(query_before, dict) else None
    after_date = query_after.get("date_raw") if isinstance(query_after, dict) else None
    restore_bookkeeping = _cold_restore_bookkeeping(
        before_driver_state,
        query_before,
        checkpoint,
    )
    query_after_history = _snapshot_history(query_after)
    persisted_after_history = _command_history(after_driver_state)
    checks = {
        "exact_one_read_only_query": bool(
            isinstance(query_envelope, dict)
            and query_envelope.get("step") == QUERY_STEP
            and query_envelope.get("accepted") is True
            and query_envelope.get("status") == "available"
        ),
        "query_source_bound_to_before_frame": _bound_route_result(
            query_before, query_envelope
        ),
        "readiness_bound_to_query_before": _same_frame(readiness, query_before),
        "single_cold_restore_bookkeeping": (
            restore_bookkeeping.get("exact") is True
        ),
        "paused_frame_unchanged": _same_frame(query_before, query_after),
        "stationary_scope_unchanged": _exact_h3937_paused_subject(query_after),
        "guarded_subject_unchanged": _guarded_subject_unchanged(
            query_before, query_after
        ),
        "exact_one_appended_query": _exact_one_appended_query(
            query_before, query_after, query_envelope
        ),
        "driver_history_matches_query_after": bool(
            query_after_history is not None
            and persisted_after_history == query_after_history
        ),
        "date_unchanged": before_date is not None and before_date == after_date,
        "checkpoint_unchanged": bool(
            after_files
            and before_files["checkpoint"]["sha256"]
            == after_files["checkpoint"]["sha256"]
        ),
        "child_pending_sidecar_unchanged": bool(
            after_files
            and before_files["child_pending_sidecar"]["sha256"]
            == after_files["child_pending_sidecar"]["sha256"]
        ),
        "abi_unchanged": bool(
            after_files
            and all(
                before_files[key]["sha256"] == after_files[key]["sha256"]
                for key in ("bridge_dll", "bridge_injector")
            )
        ),
        "cleanup_proven": cleanup.get("ok") is True,
    }
    ok = primary_error is None and all(checks.values())
    return {
        "schema": "xar.ck3.h3937-stationary-route-contact-query-run-v1",
        "ok": ok,
        "status": "GREEN_READ_ONLY" if ok else "RED",
        "read_only_query_only": True,
        "action_authorized": False,
        "round": ownership_round_id,
        "started_at": started_at,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "source": {
            "entry": "agent.py native-query-h3937-stationary-route-contact-v1",
            "capability": "game.command.query-route-contact-horizon-v1",
            "checkpoint_anchor": copy.deepcopy(checkpoint),
            "ordinary_rebind_receipt": str(rebind_receipt_path.resolve()),
            "ordinary_rebind_receipt_sha256": _sha256(rebind_receipt_path),
            "raw_source_driver_sha256": RAW_SOURCE_DRIVER_SHA256,
            "prepared_driver_sha256": before_files["driver_state"]["sha256"],
        },
        "bounds": {
            "timeout_seconds": timeout,
            "readiness_timeout_seconds": readiness_timeout,
            "query_limit": 1,
        },
        "forbidden_action_counts": {
            "close": 0,
            "marriage": 0,
            "death_terminal": 0,
            "python_successor_continuation": 0,
            "date_advance": 0,
            "gameplay": 0,
            "ui_input": 0,
        },
        "readiness": _public_binding(readiness) if isinstance(readiness, dict) else None,
        "before": {
            "files": before_files,
            "frame": copy.deepcopy(query_before),
            "date_raw": before_date,
        },
        "query_envelope": copy.deepcopy(query_envelope),
        "observed_horizon": (
            {
                "one_day_contact_free": horizon.get("one_day_contact_free"),
                "horizon_start_date_raw": horizon.get("horizon_start_date_raw"),
                "horizon_end_date_raw": horizon.get("horizon_end_date_raw"),
                "action_authorized": False,
            }
            if isinstance(horizon, dict) else None
        ),
        "after": {
            "files": after_files,
            "frame": copy.deepcopy(query_after),
            "date_raw": after_date,
        },
        "cold_restore_bookkeeping": restore_bookkeeping,
        "checks": checks,
        "cleanup": cleanup,
        "error": primary_error,
    }
