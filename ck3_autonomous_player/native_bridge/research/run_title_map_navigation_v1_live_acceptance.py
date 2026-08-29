#!/usr/bin/env python3
"""Run the title-map-navigation v1 matrix in one managed CK3 session.

The runner clones one immutable profile/save into a nonce-marked production
projection, starts exactly one supervised non-debug CK3 process, and uses only
``GameplayBridgeService.center_map_on_landed_title_v1``.  One GREEN artifact
proves c_bianzhou, b_kaifeng, repeated ``already_centered``, a typed
``title_key_not_found`` RED, unchanged camera state across that RED, frozen
EXE/DLL/injector hashes, stable full bindings, and managed cleanup.

No OCR, screen interpretation, window activation, keyboard, mouse, or
clipboard path is imported or invoked.  Production exposes no safe test-only
camera-inhibit control, so that optional negative is explicitly recorded as
skipped instead of mutating CK3 memory.
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

from xar_autoplayer.bridge.driver import BridgeUnavailableError  # noqa: E402
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.bridge.title_map_navigation_contract import (  # noqa: E402
    CENTER_MAP_ON_LANDED_TITLE_V1_CAPABILITY,
    CENTER_MAP_ON_LANDED_TITLE_V1_STEP,
    TITLE_MAP_NAVIGATION_V1_BACKEND_ID,
    TITLE_MAP_NAVIGATION_V1_COMPLETION_PREDICATE,
    TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256,
    TITLE_MAP_NAVIGATION_V1_GAME_VERSION,
    normalize_title_map_navigation_v1_binding,
)
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
NATIVE_COMMAND_TIMEOUT_SECONDS = 30.0
CONTINUE_SAVE_NAME = "autosave.ck3"
COUNTY_TITLE_KEY = "c_bianzhou"
BARONY_TITLE_KEY = "b_kaifeng"
DISPLACEMENT_TITLE_KEY = "c_guangzhou"
UNKNOWN_TITLE_KEY = "c_xar_title_map_navigation_v1_unknown"
_DISPOSABLE_MARKER_NAME = ".xar-title-map-navigation-live-clone.json"
_DISPOSABLE_KIND = "xar_title_map_navigation_v1_live_acceptance"
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
_EXPECTED_COMMAND_KEYS = (
    DISPLACEMENT_TITLE_KEY,
    COUNTY_TITLE_KEY,
    DISPLACEMENT_TITLE_KEY,
    BARONY_TITLE_KEY,
    BARONY_TITLE_KEY,
    UNKNOWN_TITLE_KEY,
    BARONY_TITLE_KEY,
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
    parser.add_argument("--expected-bridge-injector-sha256", required=True)
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
        "xar-title-map-navigation-" + uuid.uuid4().hex
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


def _prepare_live_clone(
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
        "continue_save_matches_source": _sha256_file(continue_save)
        == expected,
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


def _snapshot_binding(snapshot: object) -> dict[str, object]:
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be an object")
    diagnostics = snapshot.get("diagnostics")
    connection_generation = (
        diagnostics.get("connection_generation")
        if isinstance(diagnostics, dict)
        else None
    )
    return normalize_title_map_navigation_v1_binding(
        {
            "snapshot_id": snapshot.get("snapshot_id"),
            "revision": snapshot.get("revision"),
            "native_revision": snapshot.get("native_revision"),
            "date_raw": snapshot.get("date_raw"),
            "episode_run_id": snapshot.get("episode_run_id"),
            "connection_generation": connection_generation,
        }
    )


def _snapshot_evidence(snapshot: dict[str, object]) -> dict[str, object]:
    return {
        "binding": _snapshot_binding(snapshot),
        "paused": snapshot.get("paused"),
        "map_ready": snapshot.get("map_ready"),
        "phase": snapshot.get("phase"),
        "played_character": copy.deepcopy(snapshot.get("played_character")),
    }


def _assert_paused_map_ready(snapshot: dict[str, object]) -> None:
    if snapshot.get("paused") is not True:
        raise RuntimeError("title-map live acceptance requires pause")
    if snapshot.get("map_ready") is not True:
        raise RuntimeError("title-map live acceptance requires map-ready")


def _camera(result: object) -> dict[str, object] | None:
    if not isinstance(result, dict):
        return None
    value = result.get("camera_center")
    return copy.deepcopy(value) if isinstance(value, dict) else None


def _title_result_proof(
    result: object,
    *,
    expected_title_key: str,
    expected_binding: dict[str, object],
    allowed_statuses: set[str],
) -> dict[str, object]:
    payload = result if isinstance(result, dict) else {}
    title_value = payload.get("title")
    title = title_value if isinstance(title_value, dict) else {}
    camera_value = payload.get("camera_center")
    camera = camera_value if isinstance(camera_value, dict) else {}
    ack_value = payload.get("native_action_ack")
    ack = ack_value if isinstance(ack_value, dict) else {}
    source_value = payload.get("source")
    source = source_value if isinstance(source_value, dict) else {}
    status = payload.get("status")
    current = camera.get("current_state")
    target = camera.get("target_state")
    expected_xyz = camera.get("expected_position_xyz")
    ack_ok = bool(
        (
            status == "centered"
            and ack.get("status") == "dispatched"
            and isinstance(ack.get("sequence"), int)
            and not isinstance(ack.get("sequence"), bool)
            and int(ack["sequence"]) > 0
        )
        or (
            status == "already_centered"
            and ack
            == {
                "sequence": None,
                "status": "not_needed",
            }
        )
    )
    checks = {
        "accepted": payload.get("accepted") is True,
        "exact_step": payload.get("step")
        == CENTER_MAP_ON_LANDED_TITLE_V1_STEP,
        "allowed_status": status in allowed_statuses,
        "title_key": title.get("key") == expected_title_key,
        "title_id_positive": isinstance(title.get("title_id"), int)
        and not isinstance(title.get("title_id"), bool)
        and int(title["title_id"]) > 0,
        "title_bounds_anchor": title.get("anchor_kind")
        == "title_bounds_center",
        "full_binding": payload.get("binding") == expected_binding,
        "native_ack_matches_status": ack_ok,
        "camera_status_matches": camera.get("status") == status,
        "camera_postcondition": camera.get("postcondition_verified") is True,
        "camera_settled": camera.get("settled") is True,
        "camera_write_unblocked": camera.get("target_write_blocked") is False,
        "camera_current_target_equal": isinstance(current, list)
        and current == target,
        "camera_expected_xyz_matches": isinstance(current, list)
        and len(current) == 6
        and isinstance(expected_xyz, list)
        and len(expected_xyz) == 3
        and current[:3] == expected_xyz,
        "completion_predicate": camera.get("completion_predicate")
        == TITLE_MAP_NAVIGATION_V1_COMPLETION_PREDICATE,
        "exact_source": source
        == {
            "game_version": TITLE_MAP_NAVIGATION_V1_GAME_VERSION,
            "executable_sha256": (
                TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256
            ),
            "backend_id": TITLE_MAP_NAVIGATION_V1_BACKEND_ID,
        },
    }
    return {"checks": checks, "ok": all(checks.values())}


def _known_call(
    service: GameplayBridgeService,
    *,
    label: str,
    title_key: str,
    session_binding: dict[str, object],
    allowed_statuses: set[str],
    camera_before: dict[str, object] | None,
    camera_before_source: str | None,
) -> dict[str, object]:
    before = service.snapshot()
    _assert_paused_map_ready(before)
    before_evidence = _snapshot_evidence(before)
    result = service.center_map_on_landed_title_v1(
        title_key,
        expected_revision=int(before_evidence["binding"]["revision"]),
    )
    after = service.snapshot()
    _assert_paused_map_ready(after)
    after_evidence = _snapshot_evidence(after)
    proof = _title_result_proof(
        result,
        expected_title_key=title_key,
        expected_binding=session_binding,
        allowed_statuses=allowed_statuses,
    )
    binding_stable = bool(
        before_evidence["binding"] == session_binding
        and after_evidence["binding"] == session_binding
    )
    player_stable = (
        before_evidence["played_character"]
        == after_evidence["played_character"]
    )
    return {
        "label": label,
        "title_key": title_key,
        "before": before_evidence,
        "after": after_evidence,
        "camera_transition": {
            "before": copy.deepcopy(camera_before),
            "before_source": camera_before_source,
            "after": _camera(result),
            "initial_pre_read_exposed": camera_before is not None,
        },
        "typed_service_payload": copy.deepcopy(result),
        "typed_service_payload_sha256": _canonical_json_sha256(result),
        "result_proof": proof,
        "checks": {
            "binding_stable": binding_stable,
            "played_character_stable": player_stable,
            "result_valid": proof.get("ok") is True,
        },
        "ok": bool(binding_stable and player_stable and proof.get("ok")),
    }


def _unknown_title_call(
    service: GameplayBridgeService,
    *,
    session_binding: dict[str, object],
    camera_before: dict[str, object],
    integrity_title_key: str,
    camera_before_source: str,
) -> dict[str, object]:
    before = service.snapshot()
    _assert_paused_map_ready(before)
    before_evidence = _snapshot_evidence(before)
    error_payload: dict[str, object] | None = None
    unexpected_payload: object = None
    try:
        unexpected_payload = service.center_map_on_landed_title_v1(
            UNKNOWN_TITLE_KEY,
            expected_revision=int(before_evidence["binding"]["revision"]),
        )
    except BridgeUnavailableError as error:
        error_payload = {
            "exception_type": type(error).__name__,
            "message": str(error),
            "native_error": getattr(error, "native_error", None),
        }
    after_rejection = service.snapshot()
    _assert_paused_map_ready(after_rejection)
    after_rejection_evidence = _snapshot_evidence(after_rejection)
    integrity = _known_call(
        service,
        label="post_unknown_integrity_probe",
        title_key=integrity_title_key,
        session_binding=session_binding,
        allowed_statuses={"already_centered"},
        camera_before=camera_before,
        camera_before_source=camera_before_source,
    )
    camera_after = integrity["camera_transition"]["after"]
    checks = {
        "typed_red": bool(
            error_payload
            and error_payload.get("native_error") == "title_key_not_found"
        ),
        "no_success_payload": unexpected_payload is None,
        "binding_stable_after_rejection": bool(
            before_evidence["binding"] == session_binding
            and after_rejection_evidence["binding"] == session_binding
        ),
        "player_stable_after_rejection": (
            before_evidence["played_character"]
            == after_rejection_evidence["played_character"]
        ),
        "integrity_probe_already_centered": bool(
            integrity.get("ok") is True
            and integrity.get("typed_service_payload", {}).get("status")
            == "already_centered"
        ),
        "camera_unchanged": camera_after == camera_before,
    }
    return {
        "label": "unknown_title_typed_red",
        "title_key": UNKNOWN_TITLE_KEY,
        "before": before_evidence,
        "after_rejection": after_rejection_evidence,
        "camera_transition": {
            "before": copy.deepcopy(camera_before),
            "after": copy.deepcopy(camera_after),
            "after_source": (
                "post_unknown_integrity_probe.camera_transition.after"
            ),
        },
        "typed_error": error_payload,
        "typed_error_sha256": _canonical_json_sha256(error_payload),
        "unexpected_success_payload": unexpected_payload,
        "integrity_probe": integrity,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _history_delta(
    initial_snapshot: dict[str, object], final_snapshot: dict[str, object]
) -> list[dict[str, object]]:
    initial = initial_snapshot.get("native_command_history")
    final = final_snapshot.get("native_command_history")
    initial_rows = initial if isinstance(initial, list) else []
    final_rows = final if isinstance(final, list) else []
    if len(final_rows) < len(initial_rows):
        return []
    delta = final_rows[len(initial_rows) :]
    return copy.deepcopy(
        [row for row in delta if isinstance(row, dict)]
    )


def _run_navigation_sequence(
    service: GameplayBridgeService,
) -> dict[str, object]:
    initial = service.snapshot()
    _assert_paused_map_ready(initial)
    initial_binding = _snapshot_binding(initial)

    initial_displacement = _known_call(
        service,
        label="initial_displacement",
        title_key=DISPLACEMENT_TITLE_KEY,
        session_binding=initial_binding,
        allowed_statuses={"centered", "already_centered"},
        camera_before=None,
        camera_before_source=None,
    )
    displacement_camera = initial_displacement["camera_transition"]["after"]
    if not isinstance(displacement_camera, dict):
        raise RuntimeError("initial displacement lacks camera evidence")

    county = _known_call(
        service,
        label="county_after_displacement",
        title_key=COUNTY_TITLE_KEY,
        session_binding=initial_binding,
        allowed_statuses={"centered"},
        camera_before=displacement_camera,
        camera_before_source="initial_displacement.camera_transition.after",
    )
    county_camera = county["camera_transition"]["after"]
    if not isinstance(county_camera, dict):
        raise RuntimeError("county result lacks camera evidence")

    second_displacement = _known_call(
        service,
        label="displacement_after_county",
        title_key=DISPLACEMENT_TITLE_KEY,
        session_binding=initial_binding,
        allowed_statuses={"centered"},
        camera_before=county_camera,
        camera_before_source="county_after_displacement.camera_transition.after",
    )
    second_displacement_camera = second_displacement[
        "camera_transition"
    ]["after"]
    if not isinstance(second_displacement_camera, dict):
        raise RuntimeError("second displacement lacks camera evidence")

    barony = _known_call(
        service,
        label="barony_after_displacement",
        title_key=BARONY_TITLE_KEY,
        session_binding=initial_binding,
        allowed_statuses={"centered"},
        camera_before=second_displacement_camera,
        camera_before_source=(
            "displacement_after_county.camera_transition.after"
        ),
    )
    barony_camera = barony["camera_transition"]["after"]
    if not isinstance(barony_camera, dict):
        raise RuntimeError("barony result lacks camera evidence")

    repeat_barony = _known_call(
        service,
        label="barony_repeat",
        title_key=BARONY_TITLE_KEY,
        session_binding=initial_binding,
        allowed_statuses={"already_centered"},
        camera_before=barony_camera,
        camera_before_source="barony_after_displacement.camera_transition.after",
    )
    stable_camera = repeat_barony["camera_transition"]["after"]
    if not isinstance(stable_camera, dict):
        raise RuntimeError("repeated barony result lacks camera evidence")

    unknown = _unknown_title_call(
        service,
        session_binding=initial_binding,
        camera_before=stable_camera,
        integrity_title_key=BARONY_TITLE_KEY,
        camera_before_source="barony_repeat.camera_transition.after",
    )
    final = service.snapshot()
    _assert_paused_map_ready(final)
    final_binding = _snapshot_binding(final)
    history_delta = _history_delta(initial, final)
    history_commands = [row.get("command") for row in history_delta]
    history_outcomes = [row.get("ok") for row in history_delta]

    displacement_payload = initial_displacement.get(
        "typed_service_payload"
    )
    displacement_title = (
        displacement_payload.get("title")
        if isinstance(displacement_payload, dict)
        else None
    )
    displacement_title = (
        displacement_title if isinstance(displacement_title, dict) else {}
    )
    county_payload = county.get("typed_service_payload")
    county_title = (
        county_payload.get("title")
        if isinstance(county_payload, dict)
        else None
    )
    county_title = county_title if isinstance(county_title, dict) else {}
    barony_payload = barony.get("typed_service_payload")
    barony_title = (
        barony_payload.get("title")
        if isinstance(barony_payload, dict)
        else None
    )
    barony_title = barony_title if isinstance(barony_title, dict) else {}
    known_title_checks = {
        "displacement_key_and_tier": displacement_title.get("key")
        == DISPLACEMENT_TITLE_KEY
        and displacement_title.get("tier_key") == "county",
        "county_key_and_tier": county_title.get("key") == COUNTY_TITLE_KEY
        and county_title.get("tier_key") == "county",
        "barony_key_and_tier": barony_title.get("key") == BARONY_TITLE_KEY
        and barony_title.get("tier_key") == "barony",
        "distinct_title_ids": county_title.get("title_id")
        != barony_title.get("title_id"),
        "distinct_title_bounds": county_title.get("bounds_extent")
        != barony_title.get("bounds_extent"),
        "displacement_differs_from_county_camera": (
            initial_displacement.get("camera_transition", {})
            .get("after", {})
            .get("expected_position_xyz")
            != county.get("camera_transition", {})
            .get("after", {})
            .get("expected_position_xyz")
        ),
        "displacement_differs_from_barony_camera": (
            second_displacement.get("camera_transition", {})
            .get("after", {})
            .get("expected_position_xyz")
            != barony.get("camera_transition", {})
            .get("after", {})
            .get("expected_position_xyz")
        ),
    }
    steps = [
        initial_displacement,
        county,
        second_displacement,
        barony,
        repeat_barony,
    ]
    attempted_title_keys = [row.get("title_key") for row in steps] + [
        unknown.get("title_key"),
        unknown.get("integrity_probe", {}).get("title_key"),
    ]
    camera_pairs = [
        row.get("camera_transition", {}) for row in steps[1:]
    ] + [unknown.get("camera_transition", {})]
    checks = {
        "initial_displacement_valid": initial_displacement.get("ok") is True,
        "county_dispatched_from_displacement": bool(
            county.get("ok") is True
            and county.get("typed_service_payload", {}).get("status")
            == "centered"
        ),
        "second_displacement_dispatched": bool(
            second_displacement.get("ok") is True
            and second_displacement.get(
                "typed_service_payload", {}
            ).get("status")
            == "centered"
        ),
        "barony_dispatched_from_displacement": bool(
            barony.get("ok") is True
            and barony.get("typed_service_payload", {}).get("status")
            == "centered"
        ),
        "repeat_already_centered": bool(
            repeat_barony.get("ok") is True
            and repeat_barony.get("typed_service_payload", {}).get("status")
            == "already_centered"
        ),
        "known_title_identity": all(known_title_checks.values()),
        "unknown_title_typed_red_and_camera_unchanged": unknown.get("ok")
        is True,
        "all_known_steps_valid": all(row.get("ok") is True for row in steps),
        "exact_typed_title_key_sequence": attempted_title_keys
        == list(_EXPECTED_COMMAND_KEYS),
        "full_camera_before_after_recorded": all(
            isinstance(pair, dict)
            and isinstance(pair.get("before"), dict)
            and isinstance(pair.get("after"), dict)
            for pair in camera_pairs
        ),
        "full_typed_payloads_recorded": all(
            isinstance(row.get("typed_service_payload"), dict)
            and isinstance(row.get("typed_service_payload_sha256"), str)
            for row in steps
        ),
        "full_binding_stable": final_binding == initial_binding,
        "played_character_stable": initial.get("played_character")
        == final.get("played_character"),
        "exact_driver_history_commands": history_commands
        == [CENTER_MAP_ON_LANDED_TITLE_V1_STEP] * len(_EXPECTED_COMMAND_KEYS),
        "exact_driver_history_outcomes": history_outcomes
        == [True, True, True, True, True, False, True],
        "raw_driver_history_present": len(history_delta)
        == len(_EXPECTED_COMMAND_KEYS),
    }
    return {
        "session_binding": initial_binding,
        "initial_snapshot": _snapshot_evidence(initial),
        "final_snapshot": _snapshot_evidence(final),
        "expected_command_title_keys": list(_EXPECTED_COMMAND_KEYS),
        "attempted_title_keys": attempted_title_keys,
        "known_title_checks": known_title_checks,
        "known_steps": steps,
        "unknown_step": unknown,
        "raw_native_driver_history_delta": history_delta,
        "raw_native_driver_history_sha256": _canonical_json_sha256(
            history_delta
        ),
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
    injector_sha256: str,
    expected_injector_sha256: str,
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
        == TITLE_MAP_NAVIGATION_V1_GAME_VERSION,
        "adapter_id": hello.get("game_adapter_id") == EXPECTED_ADAPTER_ID,
        "adapter_ready": hello.get("game_adapter_status") == "ready",
        "build_match": hello.get("ck3_build_match") is True,
        "hello_executable_sha256": isinstance(observed_sha, str)
        and observed_sha.upper()
        == TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256,
        "managed_executable_sha256": managed_executable_sha256.upper()
        == TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256,
        "production_dll_sha256": production_dll_sha256.upper()
        == expected_production_dll_sha256.upper(),
        "injector_sha256": injector_sha256.upper()
        == expected_injector_sha256.upper(),
    }
    return {
        "expected_game_version": TITLE_MAP_NAVIGATION_V1_GAME_VERSION,
        "expected_adapter_id": EXPECTED_ADAPTER_ID,
        "expected_executable_sha256": (
            TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256
        ),
        "expected_production_dll_sha256": expected_production_dll_sha256,
        "expected_injector_sha256": expected_injector_sha256,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _capability_proof(capabilities: object) -> dict[str, object]:
    raw = capabilities if isinstance(capabilities, dict) else {}
    advertised_value = raw.get("bridge_capabilities")
    advertised = advertised_value if isinstance(advertised_value, list) else []
    hello_value = _diagnostics(raw).get("hello")
    hello = hello_value if isinstance(hello_value, dict) else {}
    hello_capabilities_value = hello.get("capabilities")
    hello_capabilities = (
        hello_capabilities_value
        if isinstance(hello_capabilities_value, list)
        else []
    )
    action_steps_value = raw.get("action_steps")
    action_steps = (
        action_steps_value if isinstance(action_steps_value, list) else []
    )
    checks = {
        "native_headless_backend": raw.get("backend_id") == PURE_NATIVE_MODE,
        "bridge_capability": CENTER_MAP_ON_LANDED_TITLE_V1_CAPABILITY
        in advertised,
        "hello_capability": CENTER_MAP_ON_LANDED_TITLE_V1_CAPABILITY
        in hello_capabilities,
        "explicit_only_not_action_step": CENTER_MAP_ON_LANDED_TITLE_V1_STEP
        not in action_steps,
    }
    return {
        "required_bridge_capability": (
            CENTER_MAP_ON_LANDED_TITLE_V1_CAPABILITY
        ),
        "forbidden_generic_action_step": CENTER_MAP_ON_LANDED_TITLE_V1_STEP,
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


def _inhibit_negative_report() -> dict[str, object]:
    return {
        "status": "skipped",
        "executed": False,
        "acceptable_for_gate": True,
        "reason": (
            "production exposes no typed, reversible camera-inhibit control; "
            "camera+0x777 injection remains native offline-fixture only"
        ),
        "process_memory_modified": False,
        "live_claim": False,
    }


def _interaction_audit() -> dict[str, object]:
    counters = {
        "ocr_calls": 0,
        "screen_or_pixel_judgment_calls": 0,
        "window_activation_calls": 0,
        "keyboard_calls": 0,
        "mouse_calls": 0,
        "clipboard_calls": 0,
    }
    return {
        "formal_path": (
            "GameplayBridgeService.center_map_on_landed_title_v1 -> "
            "NativeHeadlessGameplayDriver.center_map_on_landed_title_v1"
        ),
        "fallbacks_enabled": False,
        "counters": counters,
        "all_zero": all(value == 0 for value in counters.values()),
    }


def _run_live_stage(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    expected_dll_sha256: str,
    expected_injector_sha256: str,
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
        if executable_sha256 != TITLE_MAP_NAVIGATION_V1_EXECUTABLE_SHA256:
            raise RuntimeError("managed CK3 executable SHA-256 differs")
        if dll_sha256 != expected_dll_sha256:
            raise RuntimeError("production bridge DLL SHA-256 differs")
        if injector_sha256 != expected_injector_sha256:
            raise RuntimeError("production bridge injector SHA-256 differs")

        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
            command_timeout_seconds=NATIVE_COMMAND_TIMEOUT_SECONDS,
        )
        service = GameplayBridgeService(driver)
        session_thread = threading.Thread(
            target=supervise,
            name="xar-title-map-navigation-live-session",
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
            injector_sha256=injector_sha256,
            expected_injector_sha256=expected_injector_sha256,
        )
        capability = _capability_proof(capabilities_before)
        if exact_binary.get("ok") is not True:
            raise RuntimeError("exact EXE/DLL/injector build proof failed")
        if capability.get("ok") is not True:
            raise RuntimeError("title-map navigation capability is incomplete")
        sequence = _run_navigation_sequence(service)
        if sequence.get("ok") is not True:
            raise RuntimeError("title-map navigation matrix failed")
        capabilities_after = driver.capabilities()
        same_process = _same_process_proof(
            capabilities_before, capabilities_after
        )
        if same_process.get("ok") is not True:
            raise RuntimeError("title-map matrix crossed bridge process")
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
        and int(session_value.get("pid", 0)) > 0,
        "session_pid_matches_bridge_pid": session_value.get("pid")
        == bridge_pid,
        "no_managed_restarts": session_value.get("restart_count") == 0
        and session_value.get("restart_shutdowns") in (None, []),
        "same_process_matrix": bool(
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
        "stage": "production-paused-title-map-navigation",
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
            "game_version": TITLE_MAP_NAVIGATION_V1_GAME_VERSION,
            "game_executable": str(spec.game_exe.resolve()),
            "game_executable_sha256": executable_sha256,
            "bridge_dll": str(config.dll_path),
            "bridge_dll_sha256": dll_sha256,
            "expected_bridge_dll_sha256": expected_dll_sha256,
            "bridge_injector": str(config.injector_path),
            "bridge_injector_sha256": injector_sha256,
            "expected_bridge_injector_sha256": expected_injector_sha256,
        },
        "capabilities_before": capabilities_before,
        "capabilities_after": capabilities_after,
        "exact_binary_proof": exact_binary,
        "capability_proof": capability,
        "same_process_proof": same_process,
        "navigation_sequence": sequence,
        "interaction_audit": _interaction_audit(),
        "inhibit_negative": _inhibit_negative_report(),
        "managed_process_proof": managed_process,
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
    expected_injector_sha256 = _canonical_sha256(
        args.expected_bridge_injector_sha256,
        "expected bridge injector SHA-256",
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
        spec, clone = _prepare_live_clone(
            source_profile=source_profile,
            target_state_dir=target_root / "run",
            game_dir=args.game_dir.expanduser().resolve(),
            source_save=source_save,
        )
        stage = _run_live_stage(
            spec=spec,
            config=config,
            expected_dll_sha256=expected_dll_sha256,
            expected_injector_sha256=expected_injector_sha256,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
        )
        if stage.get("ok") is not True:
            raise RuntimeError(
                str(stage.get("error") or "title-map live stage failed")
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
    sequence = (
        stage.get("navigation_sequence") if isinstance(stage, dict) else None
    )
    sequence = sequence if isinstance(sequence, dict) else {}
    interaction = (
        stage.get("interaction_audit") if isinstance(stage, dict) else None
    )
    interaction = interaction if isinstance(interaction, dict) else {}
    inhibit = (
        stage.get("inhibit_negative") if isinstance(stage, dict) else None
    )
    inhibit = inhibit if isinstance(inhibit, dict) else {}
    ok = bool(
        primary_error is None
        and stage
        and stage.get("ok") is True
        and source_unchanged
        and cleanup.get("ok") is True
        and interaction.get("all_zero") is True
        and inhibit.get("acceptable_for_gate") is True
    )
    payload: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_title_map_navigation_v1_live_acceptance",
        "started_at": started_wall,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "ok": ok,
        "bounds": {
            "timeout_seconds": timeout,
            "readiness_timeout_seconds": readiness_timeout,
            "native_command_timeout_seconds": (
                NATIVE_COMMAND_TIMEOUT_SECONDS
            ),
        },
        "policy": {
            "production_non_debug": True,
            "load_kind": "continue_immutable_source_save",
            "single_managed_ck3_session": True,
            "typed_service_api_only": True,
            "expected_command_title_keys": list(_EXPECTED_COMMAND_KEYS),
            "generic_execute_step_used": False,
            "test_ui_or_decisions_added": False,
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
            "exact_exe_dll_injector_hashes": bool(
                stage
                and isinstance(stage.get("exact_binary_proof"), dict)
                and stage["exact_binary_proof"].get("ok") is True
            ),
            "explicit_only_capability": bool(
                stage
                and isinstance(stage.get("capability_proof"), dict)
                and stage["capability_proof"].get("ok") is True
            ),
            "single_managed_process_and_cleanup": bool(
                stage
                and isinstance(stage.get("managed_process_proof"), dict)
                and stage["managed_process_proof"].get("ok") is True
            ),
            "county_barony_and_repeat_matrix": sequence.get("ok") is True,
            "unknown_title_typed_red": bool(
                sequence
                and isinstance(sequence.get("unknown_step"), dict)
                and sequence["unknown_step"].get("checks", {}).get(
                    "typed_red"
                )
                is True
            ),
            "unknown_title_camera_unchanged": bool(
                sequence
                and isinstance(sequence.get("unknown_step"), dict)
                and sequence["unknown_step"].get("checks", {}).get(
                    "camera_unchanged"
                )
                is True
            ),
            "full_binding_stable": sequence.get("checks", {}).get(
                "full_binding_stable"
            )
            is True,
            "raw_payload_and_camera_evidence": bool(
                sequence
                and sequence.get("checks", {}).get(
                    "raw_driver_history_present"
                )
                is True
                and sequence.get("checks", {}).get(
                    "full_typed_payloads_recorded"
                )
                is True
                and sequence.get("checks", {}).get(
                    "full_camera_before_after_recorded"
                )
                is True
            ),
            "zero_ocr_keyboard_mouse_clipboard": interaction.get("all_zero")
            is True,
            "inhibit_negative_executed_or_safely_skipped": inhibit.get(
                "acceptable_for_gate"
            )
            is True,
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
