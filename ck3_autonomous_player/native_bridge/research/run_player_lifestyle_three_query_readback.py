"""Bounded, private LIFE2/focus/perk readback from one paired CK3 checkpoint.

The operator prepares a versioned candidate-manifest.json in an isolated
profile before invoking this entry. ``--preflight-only`` never starts CK3.
Live mode requires a separately allocated R{n}, sends exactly three native
read-only steps on one paused frame, and reclaims the sole CK3 process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import uuid
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_player_lifestyle_current_state_read import (
    run_owned_paused_life2_current_state_read,
)


SCHEMA = "xar.ck3.g2_m4_lifestyle_three_query_candidate_v1"
REPORT_SCHEMA = "xar.ck3.g2_m4_lifestyle_three_query_live_v1"
EXE_SHA256 = "2d00ff3101ef70b566f2fcbae292f09263199c80e9dc8f139b82d7d96f83db86"
STATE_STEP = "private-query-player-lifestyle-current-state-v1"
PERK_STEP = "private-query-player-lifestyle-formal-v1"
FOCUS_STEP = "private-query-player-lifestyle-stock-focus-v1"
PERK_ABSENT_PROGRESS_ERROR = "native_lifestyle_windowless_policy_perk_unavailable_state"


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _need(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def _write(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _frame(snapshot: dict[str, object]) -> dict[str, object]:
    played = snapshot.get("played_character")
    return {
        "snapshot_id": snapshot.get("snapshot_id"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "played_character_id": (
            played.get("character_id") if isinstance(played, dict) else None
        ),
        "played_character_alive": (
            played.get("alive") if isinstance(played, dict) else None
        ),
        "episode_run_id": snapshot.get("episode_run_id"),
        "paused": snapshot.get("paused"),
        "map_ready": snapshot.get("map_ready"),
    }


def _valid_start(frame: dict[str, object], manifest: dict[str, object]) -> bool:
    revision = frame["native_revision"]
    return bool(
        frame["paused"] is True
        and frame["map_ready"] is True
        and frame["played_character_alive"] is True
        and _positive_int(revision)
        and frame["snapshot_id"] == f"native:{revision}"
        and frame["played_character_id"] == manifest["expected_actor_id"]
        and frame["episode_run_id"] == manifest["episode_run_id"]
        and frame["date_raw"] == manifest["expected_date_raw"]
    )


def _source_commit(source: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout.strip().lower()


def _source_dirty(source: Path) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(source), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )
    return bool(completed.stdout.strip())


def _full_sha(value: object, label: str) -> str:
    text = str(value or "").lower()
    _need(
        len(text) == 40 and all(character in "0123456789abcdef" for character in text),
        f"{label} must be a full Git SHA",
    )
    return text


def _non_c_task_path(value: object, label: str) -> Path:
    _need(value is not None and bool(str(value).strip()), f"{label} is unset")
    path = Path(str(value)).resolve()
    _need(path.drive.upper() not in {"", "C:"}, f"{label} is not on a non-C drive")
    return path


def _manifest_source_identities(
    manifest: dict[str, object],
) -> dict[str, object]:
    """Validate the Python runner and native build source independently."""

    python_commit = _full_sha(
        manifest.get("python_source_commit"), "python_source_commit"
    )
    native_commit = _full_sha(
        manifest.get("native_source_commit"), "native_source_commit"
    )
    python_source = _non_c_task_path(
        manifest.get("source_repo"), "Python source checkout"
    )
    native_source = _non_c_task_path(
        manifest.get("native_source_repo"), "native source checkout"
    )
    _need(python_source.is_dir(), "Python source checkout is absent")
    _need(native_source.is_dir(), "native source checkout is absent")
    _need(
        _source_commit(python_source) == python_commit,
        "LIFE readback Python source commit differs",
    )
    _need(
        _source_commit(native_source) == native_commit,
        "LIFE readback native source commit differs",
    )
    _need(not _source_dirty(python_source), "LIFE readback Python source is dirty")
    _need(not _source_dirty(native_source), "LIFE readback native source is dirty")
    return {
        "python_source_repo": python_source,
        "python_source_commit": python_commit,
        "native_source_repo": native_source,
        "native_source_commit": native_commit,
    }


def _cache_source_root(cache_path: Path) -> Path:
    prefix = "CMAKE_HOME_DIRECTORY:INTERNAL="
    for line in cache_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith(prefix):
            return Path(line[len(prefix):]).resolve()
    raise RuntimeError("candidate CMake cache lacks its native source root")


def _verify_ordinary_profile(spec: object) -> dict[str, object]:
    from xar_autoplayer.environment import verify_profile

    return verify_profile(spec, xar_enabled="xar_off")


def _ordinary_binding(
    profile: dict[str, object], checkpoint: dict[str, object]
) -> dict[str, object]:
    from xar_autoplayer.bridge.succession_transition_contract import (
        ORDINARY_CAMPAIGN_SUCCESSION,
        bind_succession_lifecycle_from_environment_v1,
    )

    binding = bind_succession_lifecycle_from_environment_v1(
        profile,
        lifecycle=ORDINARY_CAMPAIGN_SUCCESSION,
        ordinary_campaign_no_pact=True,
    )
    _need(
        checkpoint.get("succession_lifecycle") == binding,
        "LIFE checkpoint lifecycle differs from the frozen ordinary profile",
    )
    return binding


def _prepare_path(args: argparse.Namespace, name: str) -> Path:
    value = getattr(args, name)
    _need(value is not None, f"--{name.replace('_', '-')} is required with --prepare-only")
    return _non_c_task_path(value, name.replace("_", " "))


def _copy_bound(
    source: Path, target: Path, expected_sha256: str | None, label: str
) -> str:
    _need(source.is_file(), f"{label} source is absent")
    digest = _sha(source)
    if expected_sha256 is not None:
        _need(
            digest == expected_sha256.lower(),
            f"{label} source SHA differs",
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    _need(_sha(target) == digest, f"{label} copy SHA differs")
    return digest


def prepare_candidate(args: argparse.Namespace) -> dict[str, object]:
    """Generate one fresh candidate through the production prepare/rebind path."""

    root = Path(args.candidate_root).resolve()
    _need(root.drive.upper() not in {"", "C:"}, "candidate root is not on a non-C drive")
    _need(not root.exists(), "fresh candidate root already exists")
    python_source = _prepare_path(args, "python_source_repo")
    native_source = _prepare_path(args, "native_source_repo")
    source_save = _prepare_path(args, "source_save")
    source_driver = _prepare_path(args, "source_driver")
    game_dir = _prepare_path(args, "game_dir")
    bridge_dll = _prepare_path(args, "bridge_dll")
    bridge_injector = _prepare_path(args, "bridge_injector")
    cmake_cache = _prepare_path(args, "cmake_cache")
    python_commit = _full_sha(
        args.expected_python_source_commit, "expected_python_source_commit"
    )
    native_commit = _full_sha(
        args.expected_native_source_commit, "expected_native_source_commit"
    )
    _need(_source_commit(python_source) == python_commit, "Python source commit differs")
    _need(_source_commit(native_source) == native_commit, "native source commit differs")
    _need(not _source_dirty(python_source), "Python source checkout is dirty")
    _need(not _source_dirty(native_source), "native source checkout is dirty")
    _need(
        _cache_source_root(cmake_cache)
        == (native_source / "ck3_autonomous_player" / "native_bridge").resolve(),
        "CMake cache belongs to another native source checkout",
    )
    game_exe = game_dir / "binaries" / "ck3.exe"
    _need(
        game_exe.is_file() and _sha(game_exe) == EXE_SHA256,
        "CK3 executable differs from frozen 1.19.0.6",
    )
    source_payload = json.loads(source_driver.read_text(encoding="utf-8-sig"))
    checkpoint = source_payload.get("last_checkpoint") if isinstance(source_payload, dict) else None
    _need(
        isinstance(source_payload, dict)
        and source_payload.get("format_version") == 2
        and source_payload.get("pipe_name") == args.pipe
        and source_payload.get("episode_character_id") == args.expected_actor_id
        and isinstance(source_payload.get("episode_run_id"), str)
        and isinstance(checkpoint, dict)
        and checkpoint.get("history_index") == args.expected_history_index
        and checkpoint.get("date_raw") == args.expected_date_raw,
        "source driver does not match the requested actor/date/history/pipe",
    )
    expected_save_sha = str(args.expected_source_save_sha256).lower()
    expected_driver_sha = str(args.expected_source_driver_sha256).lower()
    _need(
        len(expected_save_sha) == 64
        and len(expected_driver_sha) == 64
        and all(character in "0123456789abcdef" for character in expected_save_sha)
        and all(character in "0123456789abcdef" for character in expected_driver_sha),
        "source pair SHA pins must be lowercaseable SHA-256 values",
    )

    root.mkdir(parents=True)
    sample = root / "sample-pair"
    native = root / "native"
    state = root / "state"
    copied_save = sample / "xar_checkpoint.ck3"
    copied_driver = sample / "driver-state.json"
    copied_dll = native / "xar_ck3_bridge.dll"
    copied_injector = native / "xar_ck3_bridge_injector.exe"
    copied_cache = native / "CMakeCache.txt"
    save_sha = _copy_bound(source_save, copied_save, expected_save_sha, "source save")
    driver_sha = _copy_bound(
        source_driver, copied_driver, expected_driver_sha, "source driver"
    )
    dll_sha = _copy_bound(bridge_dll, copied_dll, None, "bridge DLL")
    injector_sha = _copy_bound(
        bridge_injector, copied_injector, None, "bridge injector"
    )
    cache_sha = _copy_bound(cmake_cache, copied_cache, None, "CMake cache")
    operator_manifest_path = root / "operator-manifest.json"
    operator_manifest: dict[str, object] = {
        "source_commit": python_commit,
        "source_repo": str(python_source),
        "python": str(Path(sys.executable).resolve()),
        "game_dir": str(game_dir),
        "state_dir": str(state),
        "pipe": args.pipe,
        "dll": str(copied_dll),
        "injector": str(copied_injector),
        "xar_enabled": "xar_off",
        "succession_lifecycle": "ordinary_campaign_succession",
        "ordinary_campaign_no_pact": True,
    }
    _write(operator_manifest_path, operator_manifest)
    operator = python_source / "tools" / "g2_preview_operator.py"
    _need(operator.is_file(), "production g2_preview_operator.py is absent")
    command = [
        str(Path(sys.executable).resolve()),
        "-B",
        str(operator),
        "prepare-state",
        "--manifest",
        str(operator_manifest_path),
        "--sample-dir",
        str(sample),
    ]
    _write(root / "prepare-command.json", {"command": command, "ck3_launched": False})
    with (root / "prepare-stdout.txt").open("w", encoding="utf-8") as stdout:
        with (root / "prepare-stderr.txt").open("w", encoding="utf-8") as stderr:
            completed = subprocess.run(
                command, stdout=stdout, stderr=stderr, check=False
            )
    _need(completed.returncode == 0, "official prepare-state failed")
    operator_manifest = json.loads(
        operator_manifest_path.read_text(encoding="utf-8-sig")
    )
    receipt_path = state / "ordinary-seed-rebind-v1.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8-sig"))
    expectations = receipt.get("no_launch_preflight_expectations")
    _need(
        receipt.get("ok") is True
        and receipt.get("ck3_launch_attempted") is False
        and isinstance(expectations, dict)
        and expectations.get("expected_character_id") == args.expected_actor_id
        and expectations.get("expected_episode_run_id")
        == source_payload["episode_run_id"]
        and expectations.get("expected_checkpoint_sha256") == save_sha
        and expectations.get("xar_enabled") == "xar_off"
        and expectations.get("succession_lifecycle")
        == "ordinary_campaign_succession"
        and expectations.get("ordinary_campaign_no_pact") is True,
        f"official prepare/rebind receipt differs from the h{args.expected_history_index} source pair",
    )
    prepared_save = state / "profile" / "save games" / "xar_checkpoint.ck3"
    prepared_driver = state / "native-session" / "driver-state.json"
    manifest: dict[str, object] = {
        "schema": SCHEMA,
        "status": "ready-no-launch",
        "read_only": True,
        "public_registered_or_advertised": False,
        "candidate_root": str(root),
        "source_repo": str(python_source),
        "python_source_commit": python_commit,
        "native_source_repo": str(native_source),
        "native_source_commit": native_commit,
        "game_dir": str(game_dir),
        "game_exe_sha256": EXE_SHA256,
        "state_dir": str(state),
        "profile_environment_sha256": operator_manifest["environment_sha256"],
        "pipe": args.pipe,
        "dll": str(copied_dll),
        "dll_sha256": dll_sha,
        "injector": str(copied_injector),
        "injector_sha256": injector_sha,
        "cmake_cache_path": str(copied_cache),
        "cmake_cache_path_sha256": cache_sha,
        "source_save": str(copied_save),
        "source_save_sha256": save_sha,
        "source_driver": str(copied_driver),
        "source_driver_sha256": driver_sha,
        "prepared_save": str(prepared_save),
        "prepared_save_sha256": _sha(prepared_save),
        "prepared_driver": str(prepared_driver),
        "prepared_driver_sha256": _sha(prepared_driver),
        "expected_actor_id": args.expected_actor_id,
        "episode_run_id": source_payload["episode_run_id"],
        "expected_date_raw": args.expected_date_raw,
        "expected_history_index": args.expected_history_index,
        "bounds": {
            "overall_seconds": 600,
            "readiness_seconds": 300,
            "native_query_seconds": 60,
        },
        "source_pair_reason": (
            f"fresh official prepare/rebind from immutable h{args.expected_history_index} source pair"
        ),
        "source_pair_receipt": str(receipt_path),
        "source_pair_receipt_sha256": _sha(receipt_path),
    }
    manifest_path = root / "candidate-manifest.json"
    _write(manifest_path, manifest)
    _spec, _verified_manifest, ready = preflight(root)
    evidence = {
        "schema": "xar.ck3.g2_m4_lifestyle_three_query_no_launch_v1",
        "status": "READY_NO_LAUNCH",
        "ck3_launched": False,
        "gameplay_actions": 0,
        "date_advanced": False,
        "candidate_manifest": str(manifest_path),
        "candidate_manifest_sha256": _sha(manifest_path),
        "python_source_commit": python_commit,
        "native_source_commit": native_commit,
        "dll_sha256": dll_sha,
        "injector_sha256": injector_sha,
        "source_save_sha256": save_sha,
        "source_driver_sha256": driver_sha,
        "prepared_driver_sha256": manifest["prepared_driver_sha256"],
        "preflight": ready,
    }
    _write(root / "NO-LAUNCH-EVIDENCE.json", evidence)
    return evidence


def _new_bound_driver(spec: Any, manifest: dict[str, object], binding: dict[str, object]) -> Any:
    from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver

    return NativeHeadlessGameplayDriver(
        str(manifest["pipe"]),
        state_dir=spec.state_dir,
        save_dir=spec.profile_dir / "save games",
        succession_lifecycle_binding=binding,
    )


def preflight(candidate_root: Path) -> tuple[object, dict[str, object], dict[str, object]]:
    root = _non_c_task_path(candidate_root, "candidate root")
    temporary = _non_c_task_path(os.environ.get("TEMP", ""), "TEMP")
    _need(
        _non_c_task_path(os.environ.get("TMP", ""), "TMP") == temporary,
        "TEMP and TMP must resolve to the same isolated non-C directory",
    )
    _need(temporary.is_dir(), "isolated non-C temporary directory is absent")
    with tempfile.TemporaryFile(dir=temporary):
        pass
    manifest = json.loads(
        (root / "candidate-manifest.json").read_text(encoding="utf-8-sig")
    )
    _need(
        isinstance(manifest, dict)
        and manifest.get("schema") == SCHEMA
        and manifest.get("status") == "ready-no-launch"
        and manifest.get("read_only") is True
        and manifest.get("public_registered_or_advertised") is False,
        "LIFE readback candidate is missing, unversioned, or advertised",
    )
    _need(
        Path(str(manifest.get("candidate_root"))).resolve() == root,
        "LIFE readback candidate belongs to another artifact root",
    )
    bounds = manifest.get("bounds")
    _need(
        isinstance(bounds, dict)
        and bounds.get("overall_seconds") == 600
        and _positive_int(bounds.get("readiness_seconds"))
        and bounds["readiness_seconds"] <= 300
        and _positive_int(bounds.get("native_query_seconds"))
        and bounds["native_query_seconds"] <= 60,
        "LIFE readback bounds must be 600/at most 300/at most 60 seconds",
    )
    identities = _manifest_source_identities(manifest)
    source = identities["python_source_repo"]
    _need(isinstance(source, Path), "Python source identity is malformed")
    sys.path[:0] = [str(source / "ck3_autonomous_player" / "src"), str(source / "tools")]
    from xar_autoplayer.bridge.native_driver import load_native_driver_state_for_resume
    from xar_autoplayer.environment import ck3_process_inventory, make_spec
    from xar_autoplayer.native_session import validate_cold_start_checkpoint_for_pipe

    state_dir = _non_c_task_path(manifest["state_dir"], "prepared state directory")
    spec = make_spec(state_dir, Path(str(manifest["game_dir"])))
    _need(
        _sha(spec.game_exe) == str(manifest["game_exe_sha256"]).lower() == EXE_SHA256,
        "CK3 executable differs from frozen 1.19.0.6",
    )
    for key in (
        "dll", "injector", "source_save", "source_driver",
        "prepared_save", "prepared_driver", "cmake_cache_path",
    ):
        _need(
            _sha(_non_c_task_path(manifest[key], key))
            == str(manifest[f"{key}_sha256"]).lower(),
            f"frozen LIFE readback {key} SHA differs",
        )
    _need(
        manifest["source_save_sha256"] == manifest["prepared_save_sha256"],
        "prepared save differs from source checkpoint",
    )
    cache_path = Path(str(manifest["cmake_cache_path"])).resolve()
    cache = cache_path.read_text(
        encoding="utf-8", errors="replace"
    )
    _need(
        "XAR_CK3_ENABLE_G2_PLAYER_LIFESTYLE_FORMAL_WIRE_PRIVATE_V1:BOOL=ON"
        in cache,
        "private LIFE slot43 feature is not ON in candidate build",
    )
    native_source = identities["native_source_repo"]
    _need(isinstance(native_source, Path), "native source identity is malformed")
    _need(
        _cache_source_root(cache_path)
        == (native_source / "ck3_autonomous_player" / "native_bridge").resolve(),
        "candidate CMake cache belongs to another native source checkout",
    )
    profile = _verify_ordinary_profile(spec)
    _need(
        profile.get("environment_sha256") == manifest["profile_environment_sha256"],
        "prepared profile fingerprint differs",
    )
    pipe = str(manifest["pipe"])
    checkpoint = validate_cold_start_checkpoint_for_pipe(spec, pipe)
    binding = _ordinary_binding(profile, checkpoint)
    driver_state = load_native_driver_state_for_resume(
        Path(str(manifest["prepared_driver"])), pipe
    )
    _need(
        isinstance(driver_state, dict)
        and checkpoint.get("sha256") == manifest["prepared_save_sha256"]
        and checkpoint.get("saved_date_raw") == manifest["expected_date_raw"]
        and checkpoint.get("history_index") == manifest["expected_history_index"]
        and driver_state.get("episode_character_id") == manifest["expected_actor_id"]
        and driver_state.get("episode_run_id") == manifest["episode_run_id"],
        "cold checkpoint actor/date/episode/history differs",
    )
    inventory = ck3_process_inventory()
    _need(not inventory.get("processes"), "CK3 instance occupies readback slot")
    return spec, manifest, {
        "status": "ready-no-launch",
        "ck3_launched": False,
        "ck3_inventory": inventory,
        "profile_environment_sha256": profile.get("environment_sha256"),
        "checkpoint": checkpoint,
        "succession_lifecycle_binding": binding,
        "episode_run_id": driver_state.get("episode_run_id"),
        "python_source_commit": identities["python_source_commit"],
        "native_source_commit": identities["native_source_commit"],
    }


def _query(
    driver: Any,
    *,
    step: str,
    source_frame: dict[str, object],
    timeout_seconds: float,
    verified_absent_progress: bool = False,
) -> dict[str, object]:
    """Send one allowlisted native read and sample a separate paused frame."""
    _need(step in {PERK_STEP, FOCUS_STEP}, "non-read-only LIFE step denied")
    request_id = "g2m4-read-" + uuid.uuid4().hex
    request = {
        "type": "execute_step",
        "protocol_version": 1,
        "request_id": request_id,
        "step": step,
        "expected_snapshot_id": source_frame["snapshot_id"],
        "expected_revision": source_frame["native_revision"],
        "expected_date_raw": source_frame["date_raw"],
        "expected_player_character_id": source_frame["played_character_id"],
        "episode_run_id": source_frame["episode_run_id"],
    }
    driver.endpoint.send(request)
    response = driver.state.wait_for_command_result(request_id, timeout_seconds)
    after = _frame(driver.take_internal_semantic_snapshot())
    record: dict[str, object] = {
        "step": step,
        "request": request,
        "response": response,
        "independent_after_frame": after,
    }
    if after != source_frame:
        return {**record, "status": "red", "issue": "paused_frame_drift"}
    if response is None:
        return {**record, "status": "timeout", "issue": "native_query_timeout"}
    if not (
        isinstance(response, dict)
        and response.get("type") == "command_result"
        and response.get("protocol_version") == 1
        and response.get("request_id") == request_id
    ):
        return {**record, "status": "red", "issue": "malformed_command_result"}
    if response.get("ok") is not True:
        if (
            step == PERK_STEP
            and verified_absent_progress
            and response.get("ok") is False
            and response.get("error") == PERK_ABSENT_PROGRESS_ERROR
        ):
            return {
                **record,
                "status": "typed_legal_unavailable",
                "native_status": PERK_ABSENT_PROGRESS_ERROR,
                "basis": "same_frame_life2_current_lifestyle_progress_absent",
            }
        return {
            **record,
            "status": "red",
            "issue": response.get("error"),
        }
    result = response.get("result")
    if not (
        isinstance(result, dict)
        and result.get("step") == step
        and result.get("private_build") is True
        and result.get("advertised") is False
        and result.get("episode_run_id") == source_frame["episode_run_id"]
    ):
        return {**record, "status": "red", "issue": "private_result_binding_invalid"}
    if step == FOCUS_STEP:
        from xar_autoplayer.bridge.player_lifestyle_private_transport_v1 import (
            parse_player_lifestyle_focus_private_v1,
        )

        typed = parse_player_lifestyle_focus_private_v1(
            response,
            expected_request_id=request_id,
            source_frame=source_frame,
            independent_after_frame=after,
        )
        if typed["status"] == "observed":
            return {
                **record,
                "status": "observed",
                "native_status": result["status"],
                "target_lifestyle_progress": typed["target_lifestyle_progress"],
            }
        if typed["status"] == "target_progress_unavailable":
            return {
                **record,
                "status": "native_unavailable",
                "native_status": "target_progress_unavailable",
                "basis": "same_frame_exact_target_getters_unavailable",
            }
        return {
            **record,
            "status": "red",
            "issue": typed.get("issue", "native_focus_read_untyped"),
            "native_status": typed.get("native_status", result.get("status")),
        }
    snapshot = result.get("snapshot")
    if (
        result.get("status") == "available"
        and isinstance(snapshot, dict)
        and snapshot.get("status") == "unavailable"
        and isinstance(snapshot.get("unavailable_reason"), str)
    ):
        return {
            **record,
            "status": "native_unavailable",
            "native_status": snapshot["unavailable_reason"],
        }
    if not (
        result.get("status") == "available"
        and isinstance(snapshot, dict)
        and snapshot.get("status") == "available"
        and snapshot.get("snapshot_id") == source_frame["snapshot_id"]
        and snapshot.get("public_revision") == source_frame["native_revision"]
        and snapshot.get("native_revision") == source_frame["native_revision"]
        and snapshot.get("proof_epoch") == source_frame["native_revision"]
        and snapshot.get("date_raw") == source_frame["date_raw"]
        and snapshot.get("player_character_id") == source_frame["played_character_id"]
        and isinstance(result.get("formal_precondition_status"), str)
    ):
        return {**record, "status": "red", "issue": "formal_result_binding_invalid"}
    candidates = snapshot.get("legal_perk_candidates")
    readiness = snapshot.get("readiness")
    if not isinstance(candidates, dict) or not isinstance(readiness, dict):
        return {**record, "status": "red", "issue": "perk_candidates_untyped"}
    if (
        candidates.get("status") == "available"
        and candidates.get("scope") == "policy_target"
        and isinstance(candidates.get("items"), list)
        and readiness.get("legal_perk_candidates_ready") is True
    ):
        return {**record, "status": "observed", "native_status": "available"}
    if (
        candidates.get("status") == "unavailable"
        and readiness.get("legal_perk_candidates_ready") is False
    ):
        return {**record, "status": "native_unavailable", "native_status": "unavailable"}
    return {**record, "status": "red", "issue": "perk_candidate_status_malformed"}


def run_three_queries(
    driver: Any,
    manifest: dict[str, object],
    evidence: Path,
    *,
    deadline: float,
) -> dict[str, object]:
    """Collect LIFE2, fixed focus and formal perk without advancing CK3."""
    starting = _frame(driver.take_internal_semantic_snapshot())
    if not _valid_start(starting, manifest):
        return {"status": "ineligible_scene", "starting_frame": starting}
    steps: list[dict[str, object]] = []
    record: dict[str, object] = {
        "status": "unexecuted",
        "starting_frame": starting,
        "steps": steps,
        "gameplay_actions": 0,
        "date_advanced": False,
    }
    verified_absent_progress = False
    for step in (STATE_STEP, FOCUS_STEP, PERK_STEP):
        remaining = deadline - time.monotonic()
        if remaining <= 20:
            record["status"] = "timeout"
            record["issue"] = "overall_window_exhausted"
            break
        timeout = min(float(manifest["bounds"]["native_query_seconds"]), remaining - 20)
        if step == STATE_STEP:
            result = run_owned_paused_life2_current_state_read(
                driver,
                str(manifest["episode_run_id"]),
                {"schema": SCHEMA, "read_only": True},
                evidence / "paused-life2-current-state.json",
                timeout_seconds=timeout,
            )
            result = dict(result)
            result["step"] = STATE_STEP
            if result.get("status") == "state_observed_final_candidates_unavailable":
                result["status"] = "observed"
            elif result.get("status") == "typed_absent_progress_evidence_insufficient":
                result["status"] = "native_unavailable"
                observed = result.get("observed")
                verified_absent_progress = (
                    isinstance(observed, dict)
                    and isinstance(observed.get("lifestyle_progress"), dict)
                    and observed["lifestyle_progress"].get("presence") == "absent"
                )
        else:
            result = _query(
                driver,
                step=step,
                source_frame=starting,
                timeout_seconds=timeout,
                verified_absent_progress=(
                    verified_absent_progress if step == PERK_STEP else False
                ),
            )
            _write(evidence / f"{step}.json", result)
        steps.append(result)
        after = _frame(driver.take_internal_semantic_snapshot())
        if after != starting:
            record.update(status="red", issue="paused_frame_drift")
            break
        if result["status"] in {"red", "timeout"}:
            record["status"] = str(result["status"])
            break
        if result["status"] == "ineligible_scene":
            record["status"] = "ineligible_scene"
            break
        if result["status"] not in {
            "observed", "native_unavailable", "typed_legal_unavailable"
        }:
            record.update(status="red", issue="unrecognized_readback_status")
            break
    else:
        statuses = [step["status"] for step in steps]
        record["status"] = (
            "three_queries_observed"
            if statuses == ["observed", "observed", "observed"]
            else "evidence_insufficient"
        )
    record["ending_frame"] = _frame(driver.take_internal_semantic_snapshot())
    record["date_advanced"] = (
        record["ending_frame"]["date_raw"] != starting["date_raw"]
    )
    if record["ending_frame"] != starting:
        record.update(status="red", issue="paused_frame_drift")
    return record


def run(candidate_root: Path, round_id: str, evidence: Path) -> int:
    spec, manifest, ready = preflight(candidate_root)
    _need(
        round_id.startswith("R") and round_id[1:].isdigit() and int(round_id[1:]) > 0,
        "sole operator must allocate a new R{n}",
    )
    evidence = _non_c_task_path(evidence, "round evidence directory")
    _need(not evidence.exists(), "round evidence directory already exists")
    evidence.mkdir(parents=True)
    started = time.monotonic()
    report: dict[str, object] = {
        "schema": REPORT_SCHEMA,
        "candidate": str(candidate_root.resolve()),
        "round_id": round_id,
        "status": "unexecuted",
        "preflight": ready,
        "python_source_commit": manifest["python_source_commit"],
        "native_source_commit": manifest["native_source_commit"],
        "game_exe_sha256": manifest["game_exe_sha256"],
        "native_dll_sha256": manifest["dll_sha256"],
        "source_save_sha256": manifest["source_save_sha256"],
        "source_driver_sha256": manifest["source_driver_sha256"],
        "public_registered_or_advertised": False,
        "gameplay_actions": 0,
        "manual_ui_inputs": 0,
        "manual_date_advance": False,
        "bounds": manifest["bounds"],
        "started_at": _now(),
    }
    locks = ExitStack()
    driver = None
    handle = None
    try:
        from xar_autoplayer.environment import ck3_process_inventory
        from xar_autoplayer.locking import exclusive_launch_lock, exclusive_state_lock
        from xar_autoplayer.native_auto_run import _wait_for_readiness
        from xar_autoplayer.runtime import NativeBridgeLaunchConfig, launch

        _need(not ck3_process_inventory().get("processes"), "old CK3 still alive")
        locks.enter_context(exclusive_launch_lock(spec.game_exe))
        locks.enter_context(exclusive_state_lock(spec.state_dir, "g2m4-three-query-readback"))
        driver = _new_bound_driver(
            spec,
            manifest,
            ready["succession_lifecycle_binding"],
        )
        handle = launch(
            spec,
            native_bridge=NativeBridgeLaunchConfig(
                mode="native-headless",
                pipe_name=str(manifest["pipe"]),
                dll_path=Path(str(manifest["dll"])),
                injector_path=Path(str(manifest["injector"])),
            ),
            continue_last_save=False,
            load_save_name="xar_checkpoint",
            verify_prepared_profile=False,
        )
        report["process"] = {
            "pid": handle.process.pid,
            "creation_date": handle.ck3_creation_date,
            "watchdog_pid": handle.watchdog_pid,
            "watchdog_creation_date": handle.watchdog_creation_date,
            "command": handle.command,
            "launched_at": _now(),
        }
        _write(evidence / "round-ownership.json", report["process"])
        report["readiness"] = _wait_for_readiness(
            driver,
            session_done=threading.Event(),
            session_state={},
            timeout_seconds=int(manifest["bounds"]["readiness_seconds"]),
            stable_seconds=1.0,
            poll_interval_seconds=0.1,
            cold_start_checkpoint=True,
            allow_terminal=False,
        )
        report["readback"] = run_three_queries(
            driver,
            manifest,
            evidence,
            deadline=started + float(manifest["bounds"]["overall_seconds"]),
        )
        report["status"] = report["readback"]["status"]
    except BaseException as error:
        report.update(
            status="red",
            red={
                "at": _now(),
                "reason": f"{type(error).__name__}: {error}",
                "traceback": traceback.format_exc(),
            },
        )
    finally:
        if handle is not None:
            try:
                from xar_autoplayer.runtime import stop_tracked

                report["cleanup"] = stop_tracked(handle, require_running=True)
            except BaseException as error:
                report["cleanup"] = {
                    "ok": False,
                    "issue": f"{type(error).__name__}: {error}",
                }
        if driver is not None:
            try:
                driver.close()
            except BaseException as error:
                report["driver_close_red"] = f"{type(error).__name__}: {error}"
        try:
            locks.close()
        except BaseException as error:
            report["lock_close_red"] = f"{type(error).__name__}: {error}"
        try:
            from xar_autoplayer.environment import ck3_process_inventory

            report["postflight"] = {
                "ck3_inventory": ck3_process_inventory(),
                "source_save_sha256": _sha(Path(str(manifest["source_save"]))),
                "wall_seconds": time.monotonic() - started,
            }
        except BaseException as error:
            report["postflight_red"] = f"{type(error).__name__}: {error}"
        cleanup = report.get("cleanup")
        post = report.get("postflight")
        reclaimed = bool(
            isinstance(cleanup, dict)
            and cleanup.get("ok") is True
            and isinstance(post, dict)
            and not post["ck3_inventory"].get("processes")
            and post["source_save_sha256"] == manifest["source_save_sha256"]
            and post["wall_seconds"] <= manifest["bounds"]["overall_seconds"]
            and not report.get("driver_close_red")
            and not report.get("lock_close_red")
        )
        report["ck3_reclaimed"] = reclaimed
        if not reclaimed:
            report["status"] = "red_cleanup" if report["status"] != "red" else "red"
        report["finished_at"] = _now()
        _write(evidence / "report.json", report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "ck3_reclaimed": report["ck3_reclaimed"],
                "evidence": str(evidence),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    if report["ck3_reclaimed"] and report["status"] == "three_queries_observed":
        return 0
    if report["ck3_reclaimed"] and report["status"] in {
        "evidence_insufficient", "timeout", "ineligible_scene"
    }:
        return 2
    return 1


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", required=True, type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--prepare-only", action="store_true")
    mode.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--python-source-repo", type=Path)
    parser.add_argument("--native-source-repo", type=Path)
    parser.add_argument("--expected-python-source-commit")
    parser.add_argument("--expected-native-source-commit")
    parser.add_argument("--source-save", type=Path)
    parser.add_argument("--source-driver", type=Path)
    parser.add_argument("--expected-source-save-sha256")
    parser.add_argument("--expected-source-driver-sha256")
    parser.add_argument("--game-dir", type=Path)
    parser.add_argument("--bridge-dll", type=Path)
    parser.add_argument("--bridge-injector", type=Path)
    parser.add_argument("--cmake-cache", type=Path)
    parser.add_argument("--pipe")
    parser.add_argument("--expected-actor-id", type=int)
    parser.add_argument("--expected-date-raw", type=int)
    parser.add_argument("--expected-history-index", type=int)
    parser.add_argument("--round")
    parser.add_argument("--evidence", type=Path)
    return parser


def main() -> int:
    args = parser().parse_args()
    if args.prepare_only:
        required = (
            "python_source_repo", "native_source_repo",
            "expected_python_source_commit", "expected_native_source_commit",
            "source_save", "source_driver", "expected_source_save_sha256",
            "expected_source_driver_sha256", "game_dir", "bridge_dll",
            "bridge_injector", "cmake_cache", "pipe", "expected_actor_id",
            "expected_date_raw", "expected_history_index",
        )
        _need(
            all(getattr(args, name) is not None for name in required),
            "--prepare-only requires the complete source/build/pair identity",
        )
        evidence = prepare_candidate(args)
        print(json.dumps(evidence, ensure_ascii=False, sort_keys=True))
        return 0
    if args.preflight_only:
        _, _, ready = preflight(args.candidate_root)
        print(json.dumps(ready, ensure_ascii=False, sort_keys=True))
        return 0
    _need(
        args.round is not None and args.evidence is not None,
        "live mode requires --round and --evidence",
    )
    return run(args.candidate_root, args.round, args.evidence.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
