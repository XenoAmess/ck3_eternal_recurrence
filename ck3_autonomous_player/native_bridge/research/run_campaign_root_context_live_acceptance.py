#!/usr/bin/env python3
"""Prove campaign-root observation survives a production cold restore.

The runner accepts one immutable CK3 profile/save/hash, creates two fresh
production projections, and never mutates the source.  Stage A issues two
same-revision campaign-root queries and saves the ordinary recovery
checkpoint.  Stage B receives only that validated checkpoint anchor, starts
from it in a new managed CK3 process, and repeats the two queries.  A GREEN
artifact requires same-frame determinism, equal campaign business values
across the cold restore, and proven cleanup of both managed process trees and
the nonce-marked disposable root.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import threading
import time
from typing import Any
import uuid


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.bridge.campaign_root_context_contract import (  # noqa: E402
    CAMPAIGN_ROOT_CONTEXT_V1_EXECUTABLE_SHA256,
    CAMPAIGN_ROOT_CONTEXT_V1_GAME_VERSION,
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
)
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.environment import (  # noqa: E402
    ensure_state_path_safe,
    is_relative_to,
    make_spec,
    paths_overlap,
    prepare_profile,
    verify_profile,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.native_auto_run import (  # noqa: E402
    _cleanup_report,
    _compact_session_report,
    _wait_for_readiness,
)
from xar_autoplayer.native_session import (  # noqa: E402
    NATIVE_DRIVER_STATE_FILENAME,
    NATIVE_SESSION_CHECKPOINT_FILENAME,
    NATIVE_SESSION_QUEUE_DIRNAME,
    native_session,
    validate_cold_start_checkpoint_for_pipe,
)
from xar_autoplayer.runtime import NativeBridgeLaunchConfig, utc_now  # noqa: E402


PURE_NATIVE_MODE = "native-headless"
EXPECTED_ADAPTER_ID = "ck3-1.19.0.6-msvc-x64"
CONTINUE_SAVE_NAME = "autosave.ck3"
SAVE_CHECKPOINT_STEP = "save-checkpoint"
_DISPOSABLE_MARKER_NAME = ".xar-campaign-root-context-live-clone.json"
_DISPOSABLE_KIND = "xar_campaign_root_context_live_acceptance"
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
    parser.add_argument("--source-profile", type=Path, required=True)
    parser.add_argument("--source-save", type=Path, required=True)
    parser.add_argument(
        "--expected-source-save-sha256", required=True
    )
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--bridge-pipe", required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument("--readiness-timeout", type=float, default=240.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--retain-state", action="store_true")
    return parser


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _expected_sha256(value: object) -> str:
    result = str(value).strip().upper()
    if not re.fullmatch(r"[0-9A-F]{64}", result):
        raise ValueError("expected source save SHA-256 must be 64 hex digits")
    return result


def _positive_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be positive")
    result = float(value)
    if result <= 0:
        raise ValueError(f"{name} must be positive")
    return result


def _target_state_dir(requested: Path | None) -> Path:
    if requested is not None:
        return requested.expanduser().resolve()
    return Path(tempfile.gettempdir()).resolve() / (
        "xar-campaign-root-context-" + uuid.uuid4().hex
    )


def _resolve_source_save(
    source_profile: Path,
    requested: Path,
    expected_sha256: str,
) -> tuple[Path, dict[str, object]]:
    profile = source_profile.expanduser().resolve()
    if not profile.is_dir():
        raise AgentError(f"immutable source profile is missing: {profile}")
    candidate = (
        requested.expanduser().resolve()
        if requested.is_absolute()
        else (profile / requested).resolve()
    )
    if not is_relative_to(candidate, profile):
        raise AgentError("source save escapes the immutable source profile")
    if not candidate.is_file():
        raise AgentError(f"source save is missing: {candidate}")
    actual = _sha256_file(candidate)
    if actual != expected_sha256:
        raise AgentError(
            f"source save SHA-256 differs: {actual} != {expected_sha256}"
        )
    return candidate, {
        "profile": str(profile),
        "path": str(candidate),
        "relative_path": candidate.relative_to(profile).as_posix(),
        "size": candidate.stat().st_size,
        "sha256": actual,
    }


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


def _prepare_disposable_root(
    target_state_dir: Path,
    *,
    source_profile: Path,
    clone_nonce: str,
) -> dict[str, object]:
    target = target_state_dir.resolve()
    source = source_profile.resolve()
    if target.exists():
        raise AgentError(f"disposable state already exists: {target}")
    ensure_state_path_safe(target)
    if paths_overlap(source, target):
        raise AgentError("source profile and disposable state overlap")
    target.mkdir(parents=True, exist_ok=False)
    marker = target / _DISPOSABLE_MARKER_NAME
    marker.write_text(
        json.dumps(
            {
                "kind": _DISPOSABLE_KIND,
                "nonce": clone_nonce,
                "source_profile": str(source),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "path": str(target),
        "marker": str(marker),
        "nonce": clone_nonce,
    }


def _prepare_stage_clone(
    *,
    source_profile: Path,
    target_state_dir: Path,
    game_dir: Path,
    source_save: Path,
    stage: str,
) -> tuple[Any, dict[str, object]]:
    target = target_state_dir.resolve()
    if target.exists():
        raise AgentError(f"{stage} clone already exists: {target}")
    if paths_overlap(source_profile.resolve(), target):
        raise AgentError(f"{stage} clone overlaps immutable source profile")
    _copy_source_profile(source_profile.resolve(), target / "profile")
    spec = make_spec(target, game_dir)
    manifest = prepare_profile(spec)
    save_dir = spec.profile_dir / "save games"
    save_dir.mkdir(parents=True, exist_ok=True)
    continue_save = save_dir / CONTINUE_SAVE_NAME
    last_save = spec.profile_dir / "last_save.ck3"
    shutil.copy2(source_save, continue_save)
    shutil.copy2(source_save, last_save)
    verified = verify_profile(spec)
    expected = _sha256_file(source_save)
    checks = {
        "continue_save_matches_source": _sha256_file(continue_save) == expected,
        "last_save_matches_source": _sha256_file(last_save) == expected,
    }
    if not all(checks.values()):
        raise AgentError(f"{stage} source checkpoint projection differs")
    mod = manifest.get("mod")
    return spec, {
        "stage": stage,
        "state_dir": str(target),
        "profile_dir": str(spec.profile_dir),
        "continue_save_name": CONTINUE_SAVE_NAME,
        "continue_save_path": str(continue_save),
        "last_save_path": str(last_save),
        "source_save_sha256": expected,
        "excluded_profile_roots": sorted(_PROFILE_ROOT_EXCLUDES),
        "environment_sha256": verified.get("environment_sha256"),
        "production_tree_sha256": (
            mod.get("production_tree_sha256")
            if isinstance(mod, dict)
            else None
        ),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _snapshot_revision(snapshot: dict[str, object]) -> int:
    value = snapshot.get("revision")
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise RuntimeError("paused snapshot lacks a public revision")
    return value


def _snapshot_date(snapshot: dict[str, object]) -> int:
    value = snapshot.get("date_raw")
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeError("paused snapshot lacks date_raw")
    return value


def _assert_paused(snapshot: dict[str, object]) -> None:
    if snapshot.get("paused") is not True:
        raise RuntimeError("campaign-root live acceptance requires pause")


def _same_paused_binding(
    before: dict[str, object], after: dict[str, object]
) -> bool:
    return bool(
        before.get("paused") is True
        and after.get("paused") is True
        and all(
            before.get(key) == after.get(key)
            for key in (
                "snapshot_id",
                "revision",
                "native_revision",
                "date_raw",
                "episode_run_id",
            )
        )
    )


def _checkpoint_forward_transition(
    before: dict[str, object], after: dict[str, object]
) -> dict[str, object]:
    before_revision = before.get("revision")
    after_revision = after.get("revision")
    before_native_revision = before.get("native_revision")
    after_native_revision = after.get("native_revision")
    before_snapshot_id = before.get("snapshot_id")
    after_snapshot_id = after.get("snapshot_id")
    checks = {
        "remained_paused": before.get("paused") is True
        and after.get("paused") is True,
        "same_date": before.get("date_raw") == after.get("date_raw"),
        "same_episode": before.get("episode_run_id")
        == after.get("episode_run_id"),
        "public_revision_advanced": isinstance(before_revision, int)
        and not isinstance(before_revision, bool)
        and isinstance(after_revision, int)
        and not isinstance(after_revision, bool)
        and after_revision > before_revision,
        "native_revision_advanced": isinstance(before_native_revision, int)
        and not isinstance(before_native_revision, bool)
        and isinstance(after_native_revision, int)
        and not isinstance(after_native_revision, bool)
        and after_native_revision > before_native_revision,
        "snapshot_identity_advanced": isinstance(before_snapshot_id, str)
        and bool(before_snapshot_id)
        and isinstance(after_snapshot_id, str)
        and bool(after_snapshot_id)
        and after_snapshot_id != before_snapshot_id,
    }
    return {
        "before": {
            "snapshot_id": before_snapshot_id,
            "revision": before_revision,
            "native_revision": before_native_revision,
            "date_raw": before.get("date_raw"),
            "episode_run_id": before.get("episode_run_id"),
            "paused": before.get("paused"),
        },
        "after": {
            "snapshot_id": after_snapshot_id,
            "revision": after_revision,
            "native_revision": after_native_revision,
            "date_raw": after.get("date_raw"),
            "episode_run_id": after.get("episode_run_id"),
            "paused": after.get("paused"),
        },
        "checks": checks,
        "ok": all(checks.values()),
    }


def _without_query_sequence(result: object) -> object:
    normalized = copy.deepcopy(result)
    if isinstance(normalized, dict):
        normalized.pop("query_sequence", None)
    return normalized


def _campaign_business_value(result: object) -> object:
    if not isinstance(result, dict):
        return None
    context = result.get("campaign_root_context")
    if not isinstance(context, dict):
        return None
    business = copy.deepcopy(context)
    business.pop("snapshot_revision", None)
    business.pop("date_raw", None)
    return business


def _checkpoint_proof(
    result: object,
    *,
    expected_date_raw: int,
) -> dict[str, object]:
    checkpoint = result.get("checkpoint") if isinstance(result, dict) else None
    checkpoint = checkpoint if isinstance(checkpoint, dict) else {}
    raw_path = checkpoint.get("path")
    path = Path(raw_path).resolve() if isinstance(raw_path, str) else None
    size = checkpoint.get("size")
    digest = checkpoint.get("sha256")
    history_index = checkpoint.get("history_index")
    file_size = path.stat().st_size if path is not None and path.is_file() else None
    file_sha256 = (
        _sha256_file(path) if path is not None and path.is_file() else None
    )
    checks = {
        "step": isinstance(result, dict)
        and result.get("step") == SAVE_CHECKPOINT_STEP,
        "saved": checkpoint.get("status") == "saved",
        "canonical_name": checkpoint.get("name")
        == NATIVE_SESSION_CHECKPOINT_FILENAME,
        "expected_date": checkpoint.get("date_raw") == expected_date_raw,
        "positive_size": isinstance(size, int)
        and not isinstance(size, bool)
        and size > 0,
        "valid_sha256": isinstance(digest, str)
        and re.fullmatch(r"[0-9a-fA-F]{64}", digest) is not None,
        "positive_history_index": isinstance(history_index, int)
        and not isinstance(history_index, bool)
        and history_index > 0,
        "materialized_file": path is not None and path.is_file(),
        "materialized_size": file_size == size,
        "materialized_sha256": isinstance(digest, str)
        and file_sha256 == digest.upper(),
    }
    return {
        "result": copy.deepcopy(result),
        "materialized_path": str(path) if path is not None else None,
        "materialized_size": file_size,
        "materialized_sha256": file_sha256,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _mutation_boundary_proof(
    commands: list[str], *, save_checkpoint: bool
) -> dict[str, object]:
    expected = [
        QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
        QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
    ]
    if save_checkpoint:
        expected.append(SAVE_CHECKPOINT_STEP)
    allowed = {
        QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
        SAVE_CHECKPOINT_STEP,
    }
    checks = {
        "only_allowed_production_commands": all(
            command in allowed for command in commands
        ),
        "exact_stage_order": commands == expected,
        "exact_two_queries": commands.count(
            QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP
        )
        == 2,
        "save_count": commands.count(SAVE_CHECKPOINT_STEP)
        == (1 if save_checkpoint else 0),
    }
    return {
        "commands": list(commands),
        "allowed_commands": sorted(allowed),
        "expected_commands": expected,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _run_double_query_sequence(
    service: GameplayBridgeService,
    *,
    save_checkpoint: bool,
) -> dict[str, object]:
    commands: list[str] = []
    before = service.snapshot()
    _assert_paused(before)
    revision = _snapshot_revision(before)
    first = service.query_campaign_root_context_v1(
        expected_revision=revision
    )
    commands.append(QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP)
    between = service.snapshot()
    second = service.query_campaign_root_context_v1(
        expected_revision=revision
    )
    commands.append(QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP)
    after_queries = service.snapshot()

    first_sequence = first.get("query_sequence")
    second_sequence = second.get("query_sequence")
    first_context = first.get("campaign_root_context")
    second_context = second.get("campaign_root_context")
    query_checks = {
        "initial_paused": before.get("paused") is True,
        "between_same_paused_binding": _same_paused_binding(before, between),
        "after_same_paused_binding": _same_paused_binding(
            before, after_queries
        ),
        "first_typed_available": first.get("status") == "available"
        and first.get("campaign_root_context_ready") is True,
        "second_typed_available": second.get("status") == "available"
        and second.get("campaign_root_context_ready") is True,
        "first_sequence_positive": isinstance(first_sequence, int)
        and not isinstance(first_sequence, bool)
        and first_sequence > 0,
        "sequence_is_exact_successor": isinstance(first_sequence, int)
        and not isinstance(first_sequence, bool)
        and isinstance(second_sequence, int)
        and not isinstance(second_sequence, bool)
        and second_sequence == first_sequence + 1,
        "normalized_contexts_equal": isinstance(first_context, dict)
        and first_context == second_context,
        "only_query_sequence_changed": _without_query_sequence(first)
        == _without_query_sequence(second),
        "result_binding_matches_revision": first.get("binding", {}).get(
            "expected_revision"
        )
        == revision
        and second.get("binding", {}).get("expected_revision") == revision,
    }

    checkpoint_result: dict[str, object] | None = None
    checkpoint: dict[str, object] | None = None
    after_save: dict[str, object] | None = None
    checkpoint_transition: dict[str, object] | None = None
    if save_checkpoint:
        checkpoint_result = service.save_checkpoint(
            expected_revision=revision
        )
        commands.append(SAVE_CHECKPOINT_STEP)
        checkpoint = _checkpoint_proof(
            checkpoint_result,
            expected_date_raw=_snapshot_date(before),
        )
        after_save = service.snapshot()
        checkpoint_transition = _checkpoint_forward_transition(
            after_queries, after_save
        )
    checkpoint_binding_ok = bool(
        not save_checkpoint
        or (
            checkpoint is not None
            and checkpoint.get("ok") is True
            and checkpoint_transition is not None
            and checkpoint_transition.get("ok") is True
        )
    )
    boundary = _mutation_boundary_proof(
        commands, save_checkpoint=save_checkpoint
    )
    checks = {
        "same_revision_double_query": all(query_checks.values()),
        "checkpoint_binding": checkpoint_binding_ok,
        "command_boundary": boundary.get("ok") is True,
    }
    return {
        "expected_revision": revision,
        "date_raw": _snapshot_date(before),
        "before_snapshot": before,
        "between_snapshot": between,
        "after_queries_snapshot": after_queries,
        "after_save_snapshot": after_save,
        "first_query": first,
        "second_query": second,
        "query_checks": query_checks,
        "checkpoint": checkpoint,
        "checkpoint_transition_proof": checkpoint_transition,
        "command_boundary_proof": boundary,
        "business_value": _campaign_business_value(first),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _diagnostics(capabilities: object) -> dict[str, object]:
    if not isinstance(capabilities, dict):
        return {}
    value = capabilities.get("diagnostics")
    return value if isinstance(value, dict) else {}


def _exact_build_proof(
    capabilities: object, managed_executable_sha256: str
) -> dict[str, object]:
    diagnostics = _diagnostics(capabilities)
    hello_value = diagnostics.get("hello")
    hello = hello_value if isinstance(hello_value, dict) else {}
    observed_sha = hello.get(
        "expected_ck3_sha256", hello.get("executable_sha256")
    )
    observed_version = hello.get(
        "expected_ck3_version", hello.get("game_version")
    )
    checks = {
        "game_version": observed_version
        == CAMPAIGN_ROOT_CONTEXT_V1_GAME_VERSION,
        "adapter_id": hello.get("game_adapter_id") == EXPECTED_ADAPTER_ID,
        "adapter_ready": hello.get("game_adapter_status") == "ready",
        "build_match": hello.get("ck3_build_match") is True,
        "hello_executable_sha256": isinstance(observed_sha, str)
        and observed_sha.upper()
        == CAMPAIGN_ROOT_CONTEXT_V1_EXECUTABLE_SHA256,
        "managed_executable_sha256": managed_executable_sha256.upper()
        == CAMPAIGN_ROOT_CONTEXT_V1_EXECUTABLE_SHA256,
    }
    return {
        "expected_game_version": CAMPAIGN_ROOT_CONTEXT_V1_GAME_VERSION,
        "expected_adapter_id": EXPECTED_ADAPTER_ID,
        "expected_executable_sha256": (
            CAMPAIGN_ROOT_CONTEXT_V1_EXECUTABLE_SHA256
        ),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _capability_proof(
    capabilities: object, *, require_save_checkpoint: bool
) -> dict[str, object]:
    raw = capabilities if isinstance(capabilities, dict) else {}
    advertised_value = raw.get("bridge_capabilities")
    advertised = advertised_value if isinstance(advertised_value, list) else []
    hello_value = _diagnostics(raw).get("hello")
    hello = hello_value if isinstance(hello_value, dict) else {}
    hello_value = hello.get("capabilities")
    hello_capabilities = hello_value if isinstance(hello_value, list) else []
    action_steps_value = raw.get("action_steps")
    action_steps = (
        action_steps_value if isinstance(action_steps_value, list) else []
    )
    required_action_steps = [QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP]
    if require_save_checkpoint:
        required_action_steps.append(SAVE_CHECKPOINT_STEP)
    required_bridge_capabilities = [
        QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY
    ]
    checks = {
        "bridge_capability": all(
            item in advertised for item in required_bridge_capabilities
        ),
        "hello_capability": all(
            item in hello_capabilities
            for item in required_bridge_capabilities
        ),
        "action_steps": all(
            item in action_steps for item in required_action_steps
        ),
        "driver_surface": raw.get(
            "campaign_root_context_v1_query_supported"
        )
        is True,
        "save_is_not_a_required_bridge_capability": (
            SAVE_CHECKPOINT_STEP not in required_bridge_capabilities
            and "game.command.save-checkpoint"
            not in required_bridge_capabilities
        ),
    }
    return {
        "required_bridge_capabilities": required_bridge_capabilities,
        "required_action_steps": required_action_steps,
        "save_checkpoint_classification": "production_action_step",
        "checks": checks,
        "ok": all(checks.values()),
    }


def _same_process_proof(
    before_capabilities: object, after_capabilities: object
) -> dict[str, object]:
    before = _diagnostics(before_capabilities)
    after = _diagnostics(after_capabilities)
    before_pid = before.get("bridge_pid")
    before_generation = before.get("connection_generation")
    checks = {
        "same_positive_bridge_pid": isinstance(before_pid, int)
        and not isinstance(before_pid, bool)
        and before_pid > 0
        and after.get("bridge_pid") == before_pid,
        "same_positive_connection_generation": isinstance(
            before_generation, int
        )
        and not isinstance(before_generation, bool)
        and before_generation > 0
        and after.get("connection_generation") == before_generation,
        "connection_remained_live": before.get("connected") is True
        and after.get("connected") is True,
    }
    return {
        "bridge_pid": before_pid,
        "connection_generation": before_generation,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _run_live_stage(
    *,
    stage: str,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    cold_start_checkpoint: bool,
    save_checkpoint: bool,
    timeout: float,
    readiness_timeout: float,
) -> dict[str, object]:
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    driver: NativeHeadlessGameplayDriver | None = None
    session_thread: threading.Thread | None = None
    session_started = False
    driver_closed = False
    readiness: dict[str, object] | None = None
    exact_build: dict[str, object] | None = None
    capability: dict[str, object] | None = None
    sequence: dict[str, object] | None = None
    same_process: dict[str, object] | None = None
    capabilities_before: dict[str, object] | None = None
    capabilities_after: dict[str, object] | None = None
    primary_error: str | None = None
    executable_sha256: str | None = None

    def supervise() -> None:
        try:
            session_state["report"] = native_session(
                spec,
                timeout_seconds=timeout + 90.0,
                native_bridge=config,
                input_stream=None,
                output_stream=None,
                poll_interval_seconds=0.05,
                cold_start_checkpoint=cold_start_checkpoint,
                stop_event=stop_event,
            )
        except BaseException as error:
            session_state["error"] = f"{type(error).__name__}: {error}"
        finally:
            session_done.set()

    try:
        executable_sha256 = _sha256_file(spec.game_exe)
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        service = GameplayBridgeService(driver)
        session_thread = threading.Thread(
            target=supervise,
            name=f"xar-campaign-root-context-{stage}",
            daemon=False,
        )
        session_thread.start()
        session_started = True
        readiness = _wait_for_readiness(
            driver,
            session_done=session_done,
            session_state=session_state,
            timeout_seconds=readiness_timeout,
            stable_seconds=0.5,
            poll_interval_seconds=0.05,
            cold_start_checkpoint=cold_start_checkpoint,
            allow_terminal=False,
        )
        capabilities_before = driver.capabilities()
        exact_build = _exact_build_proof(
            capabilities_before, executable_sha256
        )
        capability = _capability_proof(
            capabilities_before,
            require_save_checkpoint=save_checkpoint,
        )
        if exact_build.get("ok") is not True:
            raise RuntimeError(f"{stage} exact-build proof failed")
        if capability.get("ok") is not True:
            raise RuntimeError(f"{stage} campaign-root capabilities incomplete")
        sequence = _run_double_query_sequence(
            service, save_checkpoint=save_checkpoint
        )
        if sequence.get("ok") is not True:
            raise RuntimeError(f"{stage} double-query proof failed")
        capabilities_after = driver.capabilities()
        same_process = _same_process_proof(
            capabilities_before, capabilities_after
        )
        if same_process.get("ok") is not True:
            raise RuntimeError(f"{stage} crossed bridge process")
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        stop_started = time.monotonic()
        stop_event.set()
        if session_thread is not None and session_started:
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
            or f"{stage} managed process cleanup was not proven"
        )
    return {
        "stage": stage,
        "ok": bool(
            primary_error is None
            and exact_build
            and exact_build.get("ok") is True
            and capability
            and capability.get("ok") is True
            and sequence
            and sequence.get("ok") is True
            and same_process
            and same_process.get("ok") is True
            and cleanup.get("ok") is True
        ),
        "session_started": session_started,
        "cold_start_checkpoint": cold_start_checkpoint,
        "save_checkpoint": save_checkpoint,
        "readiness": readiness,
        "identity": {
            "pipe": config.pipe_name,
            "game_executable": str(spec.game_exe.resolve()),
            "game_executable_sha256": executable_sha256,
            "bridge_dll": str(config.dll_path),
            "bridge_dll_sha256": _sha256_file(config.dll_path),
            "bridge_injector": str(config.injector_path),
            "bridge_injector_sha256": _sha256_file(config.injector_path),
        },
        "capabilities_before": capabilities_before,
        "capabilities_after": capabilities_after,
        "exact_build_proof": exact_build,
        "capability_proof": capability,
        "same_process_proof": same_process,
        "sequence": sequence,
        "session": _compact_session_report(session_state.get("report")),
        "cleanup": cleanup,
        "error": primary_error,
    }


def _transfer_checkpoint_bundle(
    source_spec: Any,
    target_spec: Any,
    *,
    pipe_name: str,
) -> dict[str, object]:
    source_validation = validate_cold_start_checkpoint_for_pipe(
        source_spec, pipe_name
    )
    source_checkpoint = (
        source_spec.profile_dir
        / "save games"
        / NATIVE_SESSION_CHECKPOINT_FILENAME
    )
    source_driver_state = (
        source_spec.state_dir
        / NATIVE_SESSION_QUEUE_DIRNAME
        / NATIVE_DRIVER_STATE_FILENAME
    )
    target_checkpoint = (
        target_spec.profile_dir
        / "save games"
        / NATIVE_SESSION_CHECKPOINT_FILENAME
    )
    target_driver_state = (
        target_spec.state_dir
        / NATIVE_SESSION_QUEUE_DIRNAME
        / NATIVE_DRIVER_STATE_FILENAME
    )
    if target_checkpoint.exists() or target_driver_state.exists():
        raise AgentError("fresh Stage B already contains a cold-start anchor")
    target_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    target_driver_state.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_checkpoint, target_checkpoint)
    shutil.copy2(source_driver_state, target_driver_state)
    target_validation = validate_cold_start_checkpoint_for_pipe(
        target_spec, pipe_name
    )
    source_driver_sha = _sha256_file(source_driver_state)
    target_driver_sha = _sha256_file(target_driver_state)
    source_checkpoint_sha = _sha256_file(source_checkpoint)
    target_checkpoint_sha = _sha256_file(target_checkpoint)
    comparison_keys = (
        "name",
        "load_save_name",
        "size",
        "sha256",
        "saved_date_raw",
        "history_index",
    )
    checks = {
        "checkpoint_bytes_equal": source_checkpoint_sha
        == target_checkpoint_sha,
        "driver_state_bytes_equal": source_driver_sha == target_driver_sha,
        "source_and_target_validation_equal": all(
            source_validation.get(key) == target_validation.get(key)
            for key in comparison_keys
        ),
        "target_checkpoint_path_is_stage_b": Path(
            str(target_validation.get("path"))
        ).resolve()
        == target_checkpoint.resolve(),
    }
    return {
        "source_validation": source_validation,
        "target_validation": target_validation,
        "source_driver_state": str(source_driver_state),
        "target_driver_state": str(target_driver_state),
        "driver_state_sha256": source_driver_sha,
        "source_checkpoint": str(source_checkpoint),
        "target_checkpoint": str(target_checkpoint),
        "checkpoint_sha256": source_checkpoint_sha,
        "transferred_files": [
            NATIVE_SESSION_CHECKPOINT_FILENAME,
            f"{NATIVE_SESSION_QUEUE_DIRNAME}/{NATIVE_DRIVER_STATE_FILENAME}",
        ],
        "checks": checks,
        "ok": all(checks.values()),
    }


def _cross_stage_proof(
    stage_a: object,
    stage_b: object,
    checkpoint_transfer: object,
) -> dict[str, object]:
    a = stage_a if isinstance(stage_a, dict) else {}
    b = stage_b if isinstance(stage_b, dict) else {}
    a_sequence = a.get("sequence")
    b_sequence = b.get("sequence")
    a_sequence = a_sequence if isinstance(a_sequence, dict) else {}
    b_sequence = b_sequence if isinstance(b_sequence, dict) else {}
    transfer = (
        checkpoint_transfer
        if isinstance(checkpoint_transfer, dict)
        else {}
    )
    target_validation = transfer.get("target_validation")
    target_validation = (
        target_validation if isinstance(target_validation, dict) else {}
    )
    a_process = a.get("same_process_proof")
    b_process = b.get("same_process_proof")
    a_process = a_process if isinstance(a_process, dict) else {}
    b_process = b_process if isinstance(b_process, dict) else {}
    a_pid = a_process.get("bridge_pid")
    b_pid = b_process.get("bridge_pid")
    a_first = a_sequence.get("first_query")
    b_first = b_sequence.get("first_query")
    a_context = (
        a_first.get("campaign_root_context")
        if isinstance(a_first, dict)
        else None
    )
    b_context = (
        b_first.get("campaign_root_context")
        if isinstance(b_first, dict)
        else None
    )
    saved_date = target_validation.get("saved_date_raw")
    checks = {
        "both_stages_green": a.get("ok") is True and b.get("ok") is True,
        "cold_anchor_validated": transfer.get("ok") is True,
        "distinct_positive_managed_pids": isinstance(a_pid, int)
        and not isinstance(a_pid, bool)
        and a_pid > 0
        and isinstance(b_pid, int)
        and not isinstance(b_pid, bool)
        and b_pid > 0
        and a_pid != b_pid,
        "stage_b_is_cold_start": b.get("cold_start_checkpoint") is True,
        "stage_b_loaded_saved_date": isinstance(saved_date, int)
        and not isinstance(saved_date, bool)
        and b_sequence.get("date_raw") == saved_date,
        "campaign_business_values_equal": a_sequence.get("business_value")
        is not None
        and a_sequence.get("business_value")
        == b_sequence.get("business_value"),
        "bindings_excluded_only": isinstance(a_context, dict)
        and isinstance(b_context, dict)
        and {"snapshot_revision", "date_raw"}.issubset(a_context)
        and {"snapshot_revision", "date_raw"}.issubset(b_context),
    }
    return {
        "stage_a_bridge_pid": a_pid,
        "stage_b_bridge_pid": b_pid,
        "stage_a_snapshot_revision": (
            a_context.get("snapshot_revision")
            if isinstance(a_context, dict)
            else None
        ),
        "stage_b_snapshot_revision": (
            b_context.get("snapshot_revision")
            if isinstance(b_context, dict)
            else None
        ),
        "stage_a_date_raw": (
            a_context.get("date_raw")
            if isinstance(a_context, dict)
            else None
        ),
        "stage_b_date_raw": (
            b_context.get("date_raw")
            if isinstance(b_context, dict)
            else None
        ),
        "stage_a_business_value": a_sequence.get("business_value"),
        "stage_b_business_value": b_sequence.get("business_value"),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _cleanup_disposable_root(
    target_state_dir: Path,
    *,
    clone_nonce: str,
    retain_state: bool,
    stages: list[object],
) -> dict[str, object]:
    target = target_state_dir.resolve()
    if retain_state:
        return {
            "attempted": False,
            "removed": False,
            "path": str(target),
            "ok": False,
            "reason": "--retain-state prevents cleanup qualification",
        }
    unclean = []
    for value in stages:
        stage = value if isinstance(value, dict) else {}
        cleanup = stage.get("cleanup")
        cleanup = cleanup if isinstance(cleanup, dict) else {}
        if stage.get("session_started") is True and cleanup.get("ok") is not True:
            unclean.append(stage.get("stage"))
    if unclean:
        return {
            "attempted": False,
            "removed": False,
            "path": str(target),
            "ok": False,
            "reason": "managed process cleanup unproven for: "
            + ", ".join(str(value) for value in unclean),
        }
    marker = target / _DISPOSABLE_MARKER_NAME
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
        if not (
            payload.get("kind") == _DISPOSABLE_KIND
            and payload.get("nonce") == clone_nonce
        ):
            raise AgentError("disposable root marker differs")
        ensure_state_path_safe(target)
        shutil.rmtree(target)
        removed = not target.exists()
        return {
            "attempted": True,
            "removed": removed,
            "path": str(target),
            "ok": removed,
            "reason": None if removed else "disposable root still exists",
        }
    except BaseException as error:
        return {
            "attempted": True,
            "removed": False,
            "path": str(target),
            "ok": False,
            "reason": f"{type(error).__name__}: {error}",
        }


def _run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    started = time.monotonic()
    started_wall = utc_now()
    timeout = _positive_number(args.timeout, "timeout")
    readiness_timeout = _positive_number(
        args.readiness_timeout, "readiness_timeout"
    )
    expected_save_sha256 = _expected_sha256(
        args.expected_source_save_sha256
    )
    source_profile = args.source_profile.expanduser().resolve()
    target_root = _target_state_dir(args.state_dir)
    output = args.output.expanduser().resolve()
    if output.exists():
        raise AgentError(f"artifact output already exists: {output}")
    if is_relative_to(output, target_root):
        raise AgentError("artifact output must be outside disposable state")
    if is_relative_to(output, source_profile):
        raise AgentError("artifact output must be outside immutable source")
    clone_nonce = uuid.uuid4().hex
    config = NativeBridgeLaunchConfig(
        mode=PURE_NATIVE_MODE,
        pipe_name=args.bridge_pipe,
        dll_path=args.bridge_dll.expanduser().resolve(),
        injector_path=args.bridge_injector.expanduser().resolve(),
    )
    source_save: Path | None = None
    source_identity: dict[str, object] | None = None
    source_before: str | None = None
    disposable: dict[str, object] | None = None
    stage_a_clone: dict[str, object] | None = None
    stage_b_clone: dict[str, object] | None = None
    stage_a: dict[str, object] | None = None
    stage_b: dict[str, object] | None = None
    checkpoint_transfer: dict[str, object] | None = None
    cross_stage: dict[str, object] | None = None
    primary_error: str | None = None

    try:
        source_save, source_identity = _resolve_source_save(
            source_profile,
            args.source_save,
            expected_save_sha256,
        )
        source_before = _sha256_file(source_save)
        disposable = _prepare_disposable_root(
            target_root,
            source_profile=source_profile,
            clone_nonce=clone_nonce,
        )
        stage_a_spec, stage_a_clone = _prepare_stage_clone(
            source_profile=source_profile,
            target_state_dir=target_root / "stage-a",
            game_dir=args.game_dir.expanduser().resolve(),
            source_save=source_save,
            stage="stage-a",
        )
        stage_a = _run_live_stage(
            stage="stage-a",
            spec=stage_a_spec,
            config=config,
            cold_start_checkpoint=False,
            save_checkpoint=True,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
        )
        if stage_a.get("ok") is not True:
            raise RuntimeError(
                str(stage_a.get("error") or "Stage A live session failed")
            )
        stage_b_spec, stage_b_clone = _prepare_stage_clone(
            source_profile=source_profile,
            target_state_dir=target_root / "stage-b",
            game_dir=args.game_dir.expanduser().resolve(),
            source_save=source_save,
            stage="stage-b",
        )
        checkpoint_transfer = _transfer_checkpoint_bundle(
            stage_a_spec,
            stage_b_spec,
            pipe_name=config.pipe_name,
        )
        if checkpoint_transfer.get("ok") is not True:
            raise RuntimeError("cold checkpoint transfer did not validate")
        stage_b = _run_live_stage(
            stage="stage-b",
            spec=stage_b_spec,
            config=config,
            cold_start_checkpoint=True,
            save_checkpoint=False,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
        )
        if stage_b.get("ok") is not True:
            raise RuntimeError(
                str(stage_b.get("error") or "Stage B live session failed")
            )
        cross_stage = _cross_stage_proof(
            stage_a, stage_b, checkpoint_transfer
        )
        if cross_stage.get("ok") is not True:
            raise RuntimeError("campaign root changed across cold restore")
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"

    source_after = (
        _sha256_file(source_save)
        if source_save is not None and source_save.is_file()
        else None
    )
    source_unchanged = bool(
        source_before is not None and source_before == source_after
    )
    cleanup = (
        _cleanup_disposable_root(
            target_root,
            clone_nonce=clone_nonce,
            retain_state=bool(args.retain_state),
            stages=[stage_a, stage_b],
        )
        if target_root.exists()
        else {
            "attempted": False,
            "removed": True,
            "path": str(target_root),
            "ok": True,
            "reason": "disposable root was not materialized",
        }
    )
    if not source_unchanged and primary_error is None:
        primary_error = "immutable source save changed"
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(
            cleanup.get("reason") or "disposable cleanup was not proven"
        )
    ok = bool(
        primary_error is None
        and stage_a
        and stage_a.get("ok") is True
        and stage_b
        and stage_b.get("ok") is True
        and checkpoint_transfer
        and checkpoint_transfer.get("ok") is True
        and cross_stage
        and cross_stage.get("ok") is True
        and source_unchanged
        and cleanup.get("ok") is True
    )
    payload: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_campaign_root_context_v1_live_acceptance",
        "started_at": started_wall,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "ok": ok,
        "bounds": {
            "timeout_seconds_per_stage": timeout,
            "readiness_timeout_seconds_per_stage": readiness_timeout,
        },
        "policy": {
            "production_non_debug": True,
            "stage_a_load_kind": "continue_immutable_source_save",
            "stage_b_load_kind": "cold_start_xar_checkpoint",
            "allowed_gameplay_commands": [
                QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
                SAVE_CHECKPOINT_STEP,
            ],
            "save_checkpoint_required_as_bridge_capability": False,
            "save_checkpoint_classification": "production_action_step",
            "stage_a_expected_commands": [
                QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
                QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
                SAVE_CHECKPOINT_STEP,
            ],
            "stage_b_expected_commands": [
                QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
                QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP,
            ],
        },
        "source_save": source_identity,
        "source_save_invariant": {
            "before_sha256": source_before,
            "after_sha256": source_after,
            "unchanged": source_unchanged,
        },
        "disposable": disposable,
        "stage_a_clone": stage_a_clone,
        "stage_a": stage_a,
        "stage_b_clone": stage_b_clone,
        "checkpoint_transfer": checkpoint_transfer,
        "stage_b": stage_b,
        "cross_stage_proof": cross_stage,
        "disposable_cleanup": cleanup,
        "readiness_gates": {
            "stage_a_same_revision_double_query": bool(
                stage_a
                and isinstance(stage_a.get("sequence"), dict)
                and stage_a["sequence"].get("ok") is True
            ),
            "stage_a_checkpoint_saved": bool(
                stage_a
                and isinstance(stage_a.get("sequence"), dict)
                and isinstance(stage_a["sequence"].get("checkpoint"), dict)
                and stage_a["sequence"]["checkpoint"].get("ok") is True
            ),
            "stage_b_cold_anchor_validated": bool(
                checkpoint_transfer
                and checkpoint_transfer.get("ok") is True
            ),
            "stage_b_same_revision_double_query": bool(
                stage_b
                and isinstance(stage_b.get("sequence"), dict)
                and stage_b["sequence"].get("ok") is True
            ),
            "campaign_business_values_stable": bool(
                cross_stage and cross_stage.get("ok") is True
            ),
            "two_managed_process_trees_cleaned": bool(
                stage_a
                and isinstance(stage_a.get("cleanup"), dict)
                and stage_a["cleanup"].get("ok") is True
                and stage_b
                and isinstance(stage_b.get("cleanup"), dict)
                and stage_b["cleanup"].get("ok") is True
            ),
            "immutable_source_save_unchanged": source_unchanged,
            "nonce_disposable_cleanup": cleanup.get("ok") is True,
        },
        "error": primary_error,
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
                "cleanup": payload.get("disposable_cleanup"),
                "error": payload.get("error"),
            },
            ensure_ascii=False,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
