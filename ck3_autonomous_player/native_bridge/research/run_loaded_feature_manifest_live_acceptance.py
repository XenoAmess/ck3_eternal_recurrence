#!/usr/bin/env python3
"""Prove the exact-build loaded-feature manifest in one managed CK3 run.

The runner copies an immutable source profile/save into a nonce-marked
production projection, starts exactly one supervised non-debug CK3 process,
and performs two adjacent read-only manifest queries against one paused,
map-ready snapshot.  GREEN requires the frozen executable hash, an explicitly
supplied production DLL hash, all 44 native feature rows, canonical opaque
script-DLC keys, typed-unavailable entitlements, strict repeated-query
identity, immutable source bytes, and complete managed cleanup.

Script-DLC keys are deliberately treated as opaque UTF-8 strings.  This
acceptance does not infer ownership, entitlement, religion, faith, doctrine,
or any other gameplay meaning from a key.
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

from xar_autoplayer.bridge import (  # noqa: E402
    loaded_feature_manifest_contract as loaded_feature_contract,
)
from xar_autoplayer.bridge.loaded_feature_manifest_contract import (  # noqa: E402
    LOADED_FEATURE_MANIFEST_V1_EXECUTABLE_SHA256,
    LOADED_FEATURE_MANIFEST_V1_GAME_VERSION,
    QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY,
    QUERY_LOADED_FEATURE_MANIFEST_V1_STEP,
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
from xar_autoplayer.native_session import native_session  # noqa: E402
from xar_autoplayer.runtime import NativeBridgeLaunchConfig, utc_now  # noqa: E402


PURE_NATIVE_MODE = "native-headless"
EXPECTED_ADAPTER_ID = "ck3-1.19.0.6-msvc-x64"
CONTINUE_SAVE_NAME = "autosave.ck3"
_DISPOSABLE_MARKER_NAME = ".xar-loaded-feature-manifest-live-clone.json"
_DISPOSABLE_KIND = "xar_loaded_feature_manifest_live_acceptance"
_ALWAYS_ON_FEATURE_INDICES = frozenset({7, 11, 20, 21, 23})
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
    parser.add_argument("--expected-source-save-sha256", required=True)
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--bridge-pipe", required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--expected-bridge-dll-sha256", required=True)
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


def _canonical_sha256(value: object, name: str) -> str:
    result = str(value).strip().upper()
    if not re.fullmatch(r"[0-9A-F]{64}", result):
        raise ValueError(f"{name} must be 64 hex digits")
    return result


def _canonical_json_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


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
        "xar-loaded-feature-manifest-" + uuid.uuid4().hex
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
) -> tuple[Any, dict[str, object]]:
    target = target_state_dir.resolve()
    if target.exists():
        raise AgentError(f"live clone already exists: {target}")
    if paths_overlap(source_profile.resolve(), target):
        raise AgentError("live clone overlaps immutable source profile")
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
        raise AgentError("source checkpoint production projection differs")
    mod = manifest.get("mod")
    return spec, {
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


def _snapshot_native_revision(snapshot: dict[str, object]) -> int:
    value = snapshot.get("native_revision")
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise RuntimeError("paused snapshot lacks a positive native revision")
    return value


def _snapshot_date(snapshot: dict[str, object]) -> int:
    value = snapshot.get("date_raw")
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeError("paused snapshot lacks date_raw")
    return value


def _assert_paused_map_ready(snapshot: dict[str, object]) -> None:
    if snapshot.get("paused") is not True:
        raise RuntimeError("loaded-feature live acceptance requires pause")
    if snapshot.get("map_ready") is not True:
        raise RuntimeError("loaded-feature live acceptance requires map-ready")


def _same_paused_binding(
    before: dict[str, object], after: dict[str, object]
) -> bool:
    return bool(
        before.get("paused") is True
        and before.get("map_ready") is True
        and after.get("paused") is True
        and after.get("map_ready") is True
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


def _without_query_sequence(result: object) -> object:
    normalized = copy.deepcopy(result)
    if isinstance(normalized, dict):
        normalized.pop("query_sequence", None)
    return normalized


def _manifest_proof(
    result: object,
    *,
    expected_native_revision: int,
    expected_date_raw: int,
) -> dict[str, object]:
    envelope = result if isinstance(result, dict) else {}
    frame_value = envelope.get("loaded_feature_manifest")
    frame = frame_value if isinstance(frame_value, dict) else {}
    build_value = frame.get("build")
    build = build_value if isinstance(build_value, dict) else {}
    flags_value = frame.get("effective_feature_flags")
    flags = flags_value if isinstance(flags_value, dict) else {}
    items_value = flags.get("items")
    items = items_value if isinstance(items_value, list) else []
    expected_features = tuple(loaded_feature_contract._FEATURE_DEFINITIONS)

    exact_rows = len(items) == len(expected_features)
    enabled_popcount = 0
    if exact_rows:
        for index, (expected_id, expected_key) in enumerate(expected_features):
            item = items[index]
            if not isinstance(item, dict) or set(item) != {
                "native_index",
                "cstring_id",
                "key",
                "enabled",
            }:
                exact_rows = False
                break
            if (
                item.get("native_index") != index
                or item.get("cstring_id") != expected_id
                or item.get("key") != expected_key
                or not isinstance(item.get("enabled"), bool)
            ):
                exact_rows = False
                break
            enabled_popcount += int(item["enabled"])
    if not exact_rows:
        enabled_popcount = sum(
            1
            for item in items
            if isinstance(item, dict) and item.get("enabled") is True
        )

    always_on_enabled = bool(
        len(items) == len(expected_features)
        and all(
            isinstance(items[index], dict)
            and items[index].get("enabled") is True
            for index in _ALWAYS_ON_FEATURE_INDICES
        )
    )

    dlcs_value = frame.get("script_dlc_keys")
    dlcs = dlcs_value if isinstance(dlcs_value, dict) else {}
    keys_value = dlcs.get("keys")
    keys_are_list = isinstance(keys_value, list)
    keys = keys_value if keys_are_list else []
    valid_utf8_keys = keys_are_list
    encoded_keys: list[bytes] = []
    for key in keys:
        if (
            not isinstance(key, str)
            or not key
            or any(ord(character) < 0x20 for character in key)
        ):
            valid_utf8_keys = False
            break
        try:
            encoded = key.encode("utf-8")
        except UnicodeEncodeError:
            valid_utf8_keys = False
            break
        if len(encoded) > 1_024:
            valid_utf8_keys = False
            break
        encoded_keys.append(encoded)
    bytewise_sorted = bool(
        valid_utf8_keys and encoded_keys == sorted(encoded_keys)
    )
    unique_keys = bool(
        valid_utf8_keys and len(encoded_keys) == len(set(encoded_keys))
    )

    entitlements = frame.get("entitlements")
    readiness = frame.get("readiness")
    expected_readiness = {
        "effective_feature_flags_ready": True,
        "script_dlc_keys_ready": True,
        "entitlements_ready": False,
        "same_frame_ready": True,
        "actionable_ready": True,
    }
    expected_entitlements = {
        "status": "unavailable",
        "unavailable_reason": "store_verdict_provenance_unclosed",
        "items": None,
    }
    binding_value = envelope.get("binding")
    binding = binding_value if isinstance(binding_value, dict) else {}
    checks = {
        "typed_available": envelope.get("status") == "available"
        and envelope.get("loaded_feature_manifest_ready") is True
        and frame.get("status") == "available"
        and frame.get("unavailable_reason") is None,
        "exact_step_and_scope": envelope.get("step")
        == QUERY_LOADED_FEATURE_MANIFEST_V1_STEP
        and envelope.get("accepted") is True
        and envelope.get("scope") == "exact-loaded-feature-manifest",
        "exact_build_mirror": build
        == {
            "version": LOADED_FEATURE_MANIFEST_V1_GAME_VERSION,
            "exe_sha256": LOADED_FEATURE_MANIFEST_V1_EXECUTABLE_SHA256,
        },
        "snapshot_binding": frame.get("snapshot_revision")
        == expected_native_revision
        and frame.get("date_raw") == expected_date_raw
        and envelope.get("snapshot_revision") == expected_native_revision
        and binding.get("native_revision") == expected_native_revision
        and binding.get("date_raw") == expected_date_raw,
        "feature_component_available": flags.get("status") == "available"
        and flags.get("unavailable_reason") is None,
        "native_count_44": flags.get("native_count") == 44,
        "exact_44_native_rows": exact_rows,
        "enabled_popcount_reasonable": (
            len(_ALWAYS_ON_FEATURE_INDICES)
            <= enabled_popcount
            <= len(expected_features)
        ),
        "always_on_feature_baseline": always_on_enabled,
        "script_dlc_component_available": dlcs.get("status") == "available"
        and dlcs.get("unavailable_reason") is None,
        "script_dlc_count_matches": isinstance(
            dlcs.get("enumerated_count"), int
        )
        and not isinstance(dlcs.get("enumerated_count"), bool)
        and dlcs.get("enumerated_count") == len(keys),
        "script_dlc_keys_valid_utf8": valid_utf8_keys,
        "script_dlc_keys_unsigned_bytewise_sorted": bytewise_sorted,
        "script_dlc_keys_unique": unique_keys,
        "entitlements_typed_unavailable": entitlements
        == expected_entitlements,
        "readiness_exact": readiness == expected_readiness,
    }
    return {
        "computed_enabled_popcount": enabled_popcount,
        "always_on_feature_indices": sorted(_ALWAYS_ON_FEATURE_INDICES),
        "native_row_count": len(items),
        "script_dlc_key_count": len(keys),
        "script_dlc_key_order_sha256": _canonical_json_sha256(keys),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _run_double_query_sequence(
    service: GameplayBridgeService,
) -> dict[str, object]:
    commands: list[str] = []
    before = service.snapshot()
    _assert_paused_map_ready(before)
    revision = _snapshot_revision(before)
    native_revision = _snapshot_native_revision(before)
    date_raw = _snapshot_date(before)

    first = service.query_loaded_feature_manifest_v1(
        expected_revision=revision
    )
    commands.append(QUERY_LOADED_FEATURE_MANIFEST_V1_STEP)
    between = service.snapshot()
    second = service.query_loaded_feature_manifest_v1(
        expected_revision=revision
    )
    commands.append(QUERY_LOADED_FEATURE_MANIFEST_V1_STEP)
    after = service.snapshot()

    first_proof = _manifest_proof(
        first,
        expected_native_revision=native_revision,
        expected_date_raw=date_raw,
    )
    second_proof = _manifest_proof(
        second,
        expected_native_revision=native_revision,
        expected_date_raw=date_raw,
    )
    first_sequence = first.get("query_sequence")
    second_sequence = second.get("query_sequence")
    first_frame = first.get("loaded_feature_manifest")
    second_frame = second.get("loaded_feature_manifest")
    checks = {
        "initial_paused_map_ready": before.get("paused") is True
        and before.get("map_ready") is True,
        "between_same_paused_binding": _same_paused_binding(before, between),
        "after_same_paused_binding": _same_paused_binding(before, after),
        "first_manifest_valid": first_proof.get("ok") is True,
        "second_manifest_valid": second_proof.get("ok") is True,
        "query_sequence_exact_successor": isinstance(first_sequence, int)
        and not isinstance(first_sequence, bool)
        and first_sequence > 0
        and isinstance(second_sequence, int)
        and not isinstance(second_sequence, bool)
        and second_sequence == first_sequence + 1,
        "adjacent_manifest_frames_strictly_equal": isinstance(
            first_frame, dict
        )
        and first_frame == second_frame,
        "only_query_sequence_changed": _without_query_sequence(first)
        == _without_query_sequence(second),
        "exact_two_read_only_commands": commands
        == [
            QUERY_LOADED_FEATURE_MANIFEST_V1_STEP,
            QUERY_LOADED_FEATURE_MANIFEST_V1_STEP,
        ],
    }
    return {
        "expected_revision": revision,
        "native_revision": native_revision,
        "date_raw": date_raw,
        "before": copy.deepcopy(before),
        "between": copy.deepcopy(between),
        "after": copy.deepcopy(after),
        "first_query": copy.deepcopy(first),
        "second_query": copy.deepcopy(second),
        "first_manifest_proof": first_proof,
        "second_manifest_proof": second_proof,
        "manifest_sha256": _canonical_json_sha256(first_frame),
        "commands": commands,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _diagnostics(capabilities: object) -> dict[str, object]:
    if not isinstance(capabilities, dict):
        return {}
    value = capabilities.get("diagnostics")
    return value if isinstance(value, dict) else {}


def _exact_binary_proof(
    capabilities: object,
    *,
    managed_executable_sha256: str,
    production_dll_sha256: str,
    expected_production_dll_sha256: str,
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
        == LOADED_FEATURE_MANIFEST_V1_GAME_VERSION,
        "adapter_id": hello.get("game_adapter_id") == EXPECTED_ADAPTER_ID,
        "adapter_ready": hello.get("game_adapter_status") == "ready",
        "build_match": hello.get("ck3_build_match") is True,
        "hello_executable_sha256": isinstance(observed_sha, str)
        and observed_sha.upper()
        == LOADED_FEATURE_MANIFEST_V1_EXECUTABLE_SHA256,
        "managed_executable_sha256": managed_executable_sha256.upper()
        == LOADED_FEATURE_MANIFEST_V1_EXECUTABLE_SHA256,
        "production_dll_sha256": production_dll_sha256.upper()
        == expected_production_dll_sha256.upper(),
    }
    return {
        "expected_game_version": LOADED_FEATURE_MANIFEST_V1_GAME_VERSION,
        "expected_adapter_id": EXPECTED_ADAPTER_ID,
        "expected_executable_sha256": (
            LOADED_FEATURE_MANIFEST_V1_EXECUTABLE_SHA256
        ),
        "expected_production_dll_sha256": expected_production_dll_sha256,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _capability_proof(capabilities: object) -> dict[str, object]:
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
    checks = {
        "bridge_capability": QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY
        in advertised,
        "hello_capability": QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY
        in hello_capabilities,
        "action_step": QUERY_LOADED_FEATURE_MANIFEST_V1_STEP
        in action_steps,
        "driver_surface": raw.get(
            "loaded_feature_manifest_v1_query_supported"
        )
        is True,
    }
    return {
        "required_bridge_capability": (
            QUERY_LOADED_FEATURE_MANIFEST_V1_CAPABILITY
        ),
        "required_action_step": QUERY_LOADED_FEATURE_MANIFEST_V1_STEP,
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
    spec: Any,
    config: NativeBridgeLaunchConfig,
    expected_dll_sha256: str,
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
    exact_binary: dict[str, object] | None = None
    capability: dict[str, object] | None = None
    sequence: dict[str, object] | None = None
    same_process: dict[str, object] | None = None
    capabilities_before: dict[str, object] | None = None
    capabilities_after: dict[str, object] | None = None
    primary_error: str | None = None
    executable_sha256: str | None = None
    dll_sha256: str | None = None
    injector_sha256: str | None = None

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
        except BaseException as error:
            session_state["error"] = f"{type(error).__name__}: {error}"
        finally:
            session_done.set()

    try:
        executable_sha256 = _sha256_file(spec.game_exe)
        dll_sha256 = _sha256_file(config.dll_path)
        injector_sha256 = _sha256_file(config.injector_path)
        if (
            executable_sha256
            != LOADED_FEATURE_MANIFEST_V1_EXECUTABLE_SHA256
        ):
            raise RuntimeError("managed CK3 executable SHA-256 differs")
        if dll_sha256 != expected_dll_sha256:
            raise RuntimeError("production bridge DLL SHA-256 differs")

        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        service = GameplayBridgeService(driver)
        session_thread = threading.Thread(
            target=supervise,
            name="xar-loaded-feature-manifest-live-session",
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
            cold_start_checkpoint=False,
            allow_terminal=False,
        )
        capabilities_before = driver.capabilities()
        exact_binary = _exact_binary_proof(
            capabilities_before,
            managed_executable_sha256=executable_sha256,
            production_dll_sha256=dll_sha256,
            expected_production_dll_sha256=expected_dll_sha256,
        )
        capability = _capability_proof(capabilities_before)
        if exact_binary.get("ok") is not True:
            raise RuntimeError("exact EXE/DLL build proof failed")
        if capability.get("ok") is not True:
            raise RuntimeError("loaded-feature capabilities are incomplete")
        sequence = _run_double_query_sequence(service)
        if sequence.get("ok") is not True:
            raise RuntimeError("adjacent loaded-feature queries failed")
        capabilities_after = driver.capabilities()
        same_process = _same_process_proof(
            capabilities_before, capabilities_after
        )
        if same_process.get("ok") is not True:
            raise RuntimeError("loaded-feature query crossed bridge process")
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
            or "managed process cleanup was not proven"
        )
    session = _compact_session_report(session_state.get("report"))
    session_value = session if isinstance(session, dict) else {}
    bridge_pid = (
        same_process.get("bridge_pid")
        if isinstance(same_process, dict)
        else None
    )
    managed_process_checks = {
        "session_started": session_started,
        "positive_supervised_pid": isinstance(session_value.get("pid"), int)
        and not isinstance(session_value.get("pid"), bool)
        and session_value.get("pid", 0) > 0,
        "session_pid_matches_bridge_pid": session_value.get("pid")
        == bridge_pid,
        "same_process_query": bool(
            same_process and same_process.get("ok") is True
        ),
        "managed_cleanup": cleanup.get("ok") is True,
    }
    managed_process = {
        "session_pid": session_value.get("pid"),
        "bridge_pid": bridge_pid,
        "checks": managed_process_checks,
        "ok": all(managed_process_checks.values()),
    }
    if managed_process.get("ok") is not True and primary_error is None:
        primary_error = "managed process identity/cleanup proof failed"

    return {
        "stage": "production-paused-query",
        "ok": bool(
            primary_error is None
            and exact_binary
            and exact_binary.get("ok") is True
            and capability
            and capability.get("ok") is True
            and sequence
            and sequence.get("ok") is True
            and managed_process.get("ok") is True
        ),
        "session_started": session_started,
        "readiness": readiness,
        "identity": {
            "pipe": config.pipe_name,
            "game_executable": str(spec.game_exe.resolve()),
            "game_executable_sha256": executable_sha256,
            "bridge_dll": str(config.dll_path),
            "bridge_dll_sha256": dll_sha256,
            "expected_bridge_dll_sha256": expected_dll_sha256,
            "bridge_injector": str(config.injector_path),
            "bridge_injector_sha256": injector_sha256,
        },
        "capabilities_before": capabilities_before,
        "capabilities_after": capabilities_after,
        "exact_binary_proof": exact_binary,
        "capability_proof": capability,
        "same_process_proof": same_process,
        "managed_process_proof": managed_process,
        "sequence": sequence,
        "session": session,
        "cleanup": cleanup,
        "error": primary_error,
    }


def _cleanup_disposable_root(
    target_state_dir: Path,
    *,
    clone_nonce: str,
    retain_state: bool,
    stage: object,
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
    stage_value = stage if isinstance(stage, dict) else {}
    stage_cleanup = stage_value.get("cleanup")
    stage_cleanup = (
        stage_cleanup if isinstance(stage_cleanup, dict) else {}
    )
    if (
        stage_value.get("session_started") is True
        and stage_cleanup.get("ok") is not True
    ):
        return {
            "attempted": False,
            "removed": False,
            "path": str(target),
            "ok": False,
            "reason": "managed process cleanup is unproven",
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
    expected_save_sha256 = _canonical_sha256(
        args.expected_source_save_sha256,
        "expected source save SHA-256",
    )
    expected_dll_sha256 = _canonical_sha256(
        args.expected_bridge_dll_sha256,
        "expected bridge DLL SHA-256",
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
    source_before: dict[str, object] | None = None
    source_after: dict[str, object] | None = None
    disposable: dict[str, object] | None = None
    clone: dict[str, object] | None = None
    stage: dict[str, object] | None = None
    primary_error: str | None = None

    try:
        source_save, source_identity = _resolve_source_save(
            source_profile,
            args.source_save,
            expected_save_sha256,
        )
        source_before = {
            "size": source_save.stat().st_size,
            "sha256": _sha256_file(source_save),
        }
        disposable = _prepare_disposable_root(
            target_root,
            source_profile=source_profile,
            clone_nonce=clone_nonce,
        )
        spec, clone = _prepare_stage_clone(
            source_profile=source_profile,
            target_state_dir=target_root / "run",
            game_dir=args.game_dir.expanduser().resolve(),
            source_save=source_save,
        )
        stage = _run_live_stage(
            spec=spec,
            config=config,
            expected_dll_sha256=expected_dll_sha256,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
        )
        if stage.get("ok") is not True:
            raise RuntimeError(
                str(stage.get("error") or "loaded-feature live stage failed")
            )
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"

    if source_save is not None and source_save.is_file():
        source_after = {
            "size": source_save.stat().st_size,
            "sha256": _sha256_file(source_save),
        }
    source_unchanged = bool(
        source_before is not None
        and source_after is not None
        and source_before == source_after
        and source_after.get("sha256") == expected_save_sha256
    )
    cleanup = (
        _cleanup_disposable_root(
            target_root,
            clone_nonce=clone_nonce,
            retain_state=bool(args.retain_state),
            stage=stage,
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
        primary_error = "immutable source checkpoint bytes changed"
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(
            cleanup.get("reason") or "disposable cleanup was not proven"
        )
    sequence = stage.get("sequence") if isinstance(stage, dict) else None
    sequence = sequence if isinstance(sequence, dict) else {}
    first_proof = sequence.get("first_manifest_proof")
    first_proof = first_proof if isinstance(first_proof, dict) else {}
    ok = bool(
        primary_error is None
        and stage
        and stage.get("ok") is True
        and source_unchanged
        and cleanup.get("ok") is True
    )
    payload: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_loaded_feature_manifest_v1_live_acceptance",
        "started_at": started_wall,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "ok": ok,
        "bounds": {
            "timeout_seconds": timeout,
            "readiness_timeout_seconds": readiness_timeout,
        },
        "policy": {
            "production_non_debug": True,
            "load_kind": "continue_immutable_source_save",
            "allowed_gameplay_commands": [
                QUERY_LOADED_FEATURE_MANIFEST_V1_STEP
            ],
            "expected_commands": [
                QUERY_LOADED_FEATURE_MANIFEST_V1_STEP,
                QUERY_LOADED_FEATURE_MANIFEST_V1_STEP,
            ],
            "script_dlc_keys_are_opaque": True,
            "religion_semantics_interpreted": False,
            "ownership_or_entitlement_inferred": False,
        },
        "source_save": source_identity,
        "source_save_invariant": {
            "before": source_before,
            "after": source_after,
            "unchanged": source_unchanged,
        },
        "disposable": disposable,
        "production_clone": clone,
        "live_stage": stage,
        "disposable_cleanup": cleanup,
        "readiness_gates": {
            "exact_exe_and_dll_hash": bool(
                stage
                and isinstance(stage.get("exact_binary_proof"), dict)
                and stage["exact_binary_proof"].get("ok") is True
            ),
            "managed_process_and_cleanup": bool(
                stage
                and isinstance(stage.get("managed_process_proof"), dict)
                and stage["managed_process_proof"].get("ok") is True
            ),
            "paused_map_ready_same_frame": bool(
                sequence
                and sequence.get("checks", {}).get(
                    "initial_paused_map_ready"
                )
                is True
                and sequence.get("checks", {}).get(
                    "between_same_paused_binding"
                )
                is True
                and sequence.get("checks", {}).get(
                    "after_same_paused_binding"
                )
                is True
            ),
            "query_available": bool(
                first_proof
                and first_proof.get("checks", {}).get("typed_available")
                is True
            ),
            "complete_44_row_registry": bool(
                first_proof
                and first_proof.get("checks", {}).get(
                    "exact_44_native_rows"
                )
                is True
                and first_proof.get("checks", {}).get("native_count_44")
                is True
            ),
            "enabled_popcount_reasonable": bool(
                first_proof
                and first_proof.get("checks", {}).get(
                    "enabled_popcount_reasonable"
                )
                is True
                and first_proof.get("checks", {}).get(
                    "always_on_feature_baseline"
                )
                is True
            ),
            "opaque_script_keys_sorted": bool(
                first_proof
                and first_proof.get("checks", {}).get(
                    "script_dlc_keys_unsigned_bytewise_sorted"
                )
                is True
                and first_proof.get("checks", {}).get(
                    "script_dlc_keys_valid_utf8"
                )
                is True
                and first_proof.get("checks", {}).get(
                    "script_dlc_keys_unique"
                )
                is True
                and first_proof.get("checks", {}).get(
                    "script_dlc_count_matches"
                )
                is True
            ),
            "adjacent_queries_strictly_equal": bool(
                sequence
                and sequence.get("checks", {}).get(
                    "adjacent_manifest_frames_strictly_equal"
                )
                is True
                and sequence.get("checks", {}).get(
                    "only_query_sequence_changed"
                )
                is True
            ),
            "entitlements_typed_unavailable": bool(
                first_proof
                and first_proof.get("checks", {}).get(
                    "entitlements_typed_unavailable"
                )
                is True
            ),
            "actionable_ready_and_entitlements_not_ready": bool(
                first_proof
                and first_proof.get("checks", {}).get("readiness_exact")
                is True
            ),
            "immutable_source_checkpoint_bytes": source_unchanged,
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
