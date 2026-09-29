"""Pure no-launch admission predicates for a future R0368 managed role read.

These checks can reject a proposed source, GO, paused frame or cleanup record.
They cannot launch CK3, claim that a person saw Steam offline, or release a
task-bus resource. A separately reviewed one-shot worker is still required.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
from typing import Mapping

from .r0368_actor_army_role_operator import (
    _ASSET_SHA256, _sha256, verify_no_launch_source_pair,
)


MAIN_TASK_BUS = Path("D:/workspace/.codex-task-bus")
SCREEN_RESOURCE = "ck3-screen:acquired"
SCREEN_MAX_AGE_SECONDS = 600
GO_MAX_AGE_SECONDS = 300
TOTAL_WALL_SECONDS = 1800
CLEANUP_RESERVE_SECONDS = 240
_SHA = re.compile(r"[0-9A-Fa-f]{64}")
_TASK = re.compile(r"[a-z0-9-]+")


class AdmissionError(ValueError):
    """Typed refusal of a no-launch source or evidence contract."""


def _json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise AdmissionError(f"expected JSON object: {path}")
    return value


def _utc(value: object) -> datetime:
    if not isinstance(value, str):
        raise AdmissionError("timestamp missing")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise AdmissionError("timestamp malformed") from error
    if parsed.tzinfo is None:
        raise AdmissionError("timestamp lacks timezone")
    return parsed.astimezone(timezone.utc)


def _fresh(value: object, *, now: datetime, max_age: int) -> bool:
    try:
        age = (now.astimezone(timezone.utc) - _utc(value)).total_seconds()
    except AdmissionError:
        return False
    return -10 <= age <= max_age


def _attested_file(row: object) -> tuple[Path, str]:
    if not isinstance(row, dict) or not isinstance(row.get("path"), str):
        raise AdmissionError("attested path missing")
    digest = row.get("sha256")
    if not isinstance(digest, str) or _SHA.fullmatch(digest) is None:
        raise AdmissionError("attested SHA-256 missing")
    path = Path(row["path"])
    if _sha256(path) != digest.upper():
        raise AdmissionError("attested file bytes changed")
    return path, digest.upper()


def _same_sha256(actual: object, expected: str) -> bool:
    return (isinstance(actual, str) and _SHA.fullmatch(actual) is not None
            and actual.upper() == expected.upper())


def check_source_and_prepared_bytes(
    *, candidate_manifest: Path, release_pair_manifest: Path,
    checkout: Path, prepared_manifest: Path,
    state_dir: Path, profile_dir: Path, environment_manifest: Path,
    pipe_name: str,
) -> dict[str, object]:
    """Rehash the frozen raw pair and a distinct prepared state, without boot."""
    source = verify_no_launch_source_pair(
        candidate_manifest=candidate_manifest,
        release_pair_manifest=release_pair_manifest, checkout=checkout,
    )
    prepared = _json(prepared_manifest)
    required = {
        "checkpoint": (profile_dir / "save games" / "xar_checkpoint.ck3",
                       _ASSET_SHA256["xar_checkpoint.ck3"]),
        "sidecar": (state_dir / "player-child-matrilineal-formal-v1.json",
                    _ASSET_SHA256["player-child-matrilineal-formal-v1.json"]),
        "driver": (state_dir / "native-session" / "driver-state.json",
                   prepared.get("prepared_driver_sha256")),
        "rebind": (state_dir / "ordinary-seed-rebind-v1.json",
                   prepared.get("rebind_receipt_sha256")),
        "environment": (environment_manifest,
                        prepared.get("environment_sha256")),
    }
    if (prepared.get("schema") != "xar.war.r0368.role-only-prepared-source.v1"
            or prepared.get("status") != "READY_NO_LAUNCH"
            or prepared.get("live_authorized") is not False
            or prepared.get("ck3_launch_attempted") is not False
            or Path(str(prepared.get("state_dir"))).resolve() != state_dir.resolve()
            or Path(str(prepared.get("profile_dir"))).resolve() != profile_dir.resolve()
            or prepared.get("pipe_name") != pipe_name
            or prepared.get("candidate_manifest_sha256")
            != source["candidate_manifest_sha256"]
            or prepared.get("release_pair_manifest_sha256")
            != source["release_pair_manifest_sha256"]
            or prepared.get("raw_driver_sha256")
            != _ASSET_SHA256["driver-state.json"]):
        raise AdmissionError("prepared/source identity differs")
    hashes: dict[str, str] = {}
    for name, (path, digest) in required.items():
        if not isinstance(digest, str) or _SHA.fullmatch(digest) is None:
            raise AdmissionError(f"prepared {name} SHA-256 missing")
        actual = _sha256(path)
        if actual != digest.upper():
            raise AdmissionError(f"prepared {name} bytes changed")
        hashes[name] = actual
    rebind = _json(required["rebind"][0])
    environment_manifest_data = _json(environment_manifest)
    environment_binding_sha = environment_manifest_data.get("environment_sha256")
    if (not isinstance(environment_binding_sha, str)
            or _SHA.fullmatch(environment_binding_sha) is None):
        raise AdmissionError("prepared environment binding digest missing")
    driver = rebind.get("driver_state")
    environment = rebind.get("environment")
    save = rebind.get("save")
    if (rebind.get("schema") != "xar.ck3.ordinary-seed-rebind/v1"
            or rebind.get("ok") is not True
            or rebind.get("status") != "rebound"
            or rebind.get("ck3_launch_attempted") is not False
            or rebind.get("desktop_interaction") is not False
            or rebind.get("pipe_name") != pipe_name
            or Path(str(rebind.get("state_dir"))).resolve() != state_dir.resolve()
            or Path(str(rebind.get("profile_dir"))).resolve() != profile_dir.resolve()
            or not isinstance(driver, dict)
            or not _same_sha256(driver.get("source_sha256"),
                                _ASSET_SHA256["driver-state.json"])
            or not _same_sha256(driver.get("target_sha256"), hashes["driver"])
            or not isinstance(environment, dict)
            or not _same_sha256(environment.get("target_sha256"),
                                environment_binding_sha)
            or not isinstance(save, dict)
            or save.get("bytes_unchanged") is not True):
        raise AdmissionError("official prepared rebind receipt differs")
    return {
        "status": "PREPARED_BYTES_VERIFIED_LIVE_CLOSED",
        "source_pair_manifest_sha256": source["release_pair_manifest_sha256"],
        "prepared_manifest_sha256": _sha256(prepared_manifest),
        "prepared_hashes": hashes,
        "ck3_started": False, "screen_acquired": False, "live_go": False,
    }


def inspect_screen_lease(
    bus_dir: Path, task_id: str, *, now: datetime | None = None,
) -> dict[str, object]:
    """Read current sole owner; preserve stale records as historical evidence."""
    if bus_dir.resolve() != MAIN_TASK_BUS.resolve() or _TASK.fullmatch(task_id) is None:
        raise AdmissionError("task bus or screen task ID is not canonical")
    current = now or datetime.now(timezone.utc)
    active: list[dict[str, object]] = []
    stale: list[dict[str, object]] = []
    for path in (bus_dir / "tasks").glob("*.json"):
        row = _json(path)
        resources = row.get("resources")
        if not isinstance(resources, list):
            raise AdmissionError("task bus resource shape changed")
        if SCREEN_RESOURCE not in resources or row.get("state") == "done":
            continue
        summary = {"task_id": row.get("task_id"),
                   "state": row.get("state"),
                   "updated_at_utc": row.get("updated_at_utc"),
                   "last_sequence": row.get("last_sequence")}
        if _fresh(row.get("updated_at_utc"), now=current,
                  max_age=SCREEN_MAX_AGE_SECONDS):
            active.append(row)
        else:
            stale.append(summary)
    if (len(active) != 1 or active[0].get("task_id") != task_id
            or active[0].get("schema") != "codex.task_bus.v1"
            or active[0].get("state") != "running"
            or type(active[0].get("last_sequence")) is not int
            or active[0]["last_sequence"] <= 0):
        raise AdmissionError("sole fresh screen owner is not this attempt")
    return {"status": "SOLE_FRESH_OWNER_OBSERVED",
            "owner": {"task_id": task_id,
                      "last_sequence": active[0]["last_sequence"],
                      "updated_at_utc": active[0]["updated_at_utc"]},
            "stale_historical_tasks": stale,
            "screen_acquired_by_this_validator": False}


def inspect_go_evidence(
    go_path: Path, *, expected_round: str, expected_task_id: str,
    source_pair_sha256: str, prepared_sha256: str,
    now: datetime | None = None,
) -> dict[str, object]:
    """Verify file structure/bytes; never certify the human visual claim."""
    current = now or datetime.now(timezone.utc)
    go_sha = _sha256(go_path)
    go = _json(go_path)
    if (go.get("schema") != "xar.war.r0368.role-only-live-go.v1"
            or go.get("live_authorized") is not True
            or go.get("round") != expected_round
            or go.get("screen_task_id") != expected_task_id
            or go.get("source_pair_manifest_sha256") != source_pair_sha256
            or go.get("prepared_manifest_sha256") != prepared_sha256
            or not _fresh(go.get("issued_at_utc"), now=current,
                          max_age=GO_MAX_AGE_SECONDS)):
        raise AdmissionError("GO identity or freshness failed")
    original_path, original_sha = _attested_file(go.get("steam_original"))
    frame_path, frame_sha = _attested_file(go.get("steam_frame_receipt"))
    review_path, review_sha = _attested_file(go.get("steam_visual_review"))
    try:
        from PIL import Image
        with Image.open(original_path) as picture:
            if picture.format != "PNG":
                raise AdmissionError("Steam original is not decodable PNG")
            size = picture.size
            picture.load()
    except (OSError, ValueError) as error:
        raise AdmissionError("Steam original is not decodable PNG") from error
    if size[0] <= 0 or size[1] <= 0:
        raise AdmissionError("Steam original has invalid dimensions")
    frame = _json(frame_path)
    review = _json(review_path)
    if (frame.get("schema") != "xar.war.r0368.steam-frame-freshness.v1"
            or frame.get("status") != "fresh"
            or frame.get("steam_original_sha256") != original_sha
            or not _fresh(frame.get("captured_at_utc"), now=current,
                          max_age=SCREEN_MAX_AGE_SECONDS)
            or review.get("schema") != "xar.war.r0368.steam-offline-visual-review.v1"
            or review.get("status") != "steam_offline_fresh_reviewed"
            or review.get("steam_original_sha256") != original_sha
            or review.get("steam_frame_receipt_sha256") != frame_sha
            or review.get("reviewed_image_size") != list(size)
            or not isinstance(review.get("reviewer"), str)
            or not review["reviewer"]
            or not _fresh(review.get("reviewed_at_utc"), now=current,
                          max_age=GO_MAX_AGE_SECONDS)):
        raise AdmissionError("Steam freshness or visual-review receipt differs")
    if (_sha256(go_path) != go_sha or _sha256(original_path) != original_sha
            or _sha256(frame_path) != frame_sha
            or _sha256(review_path) != review_sha):
        raise AdmissionError("GO evidence changed during validation")
    return {
        "status": "GO_BYTES_STRUCTURALLY_VERIFIED_ONLY",
        "go_sha256": go_sha, "steam_original_sha256": original_sha,
        "steam_original_dimensions": list(size),
        "frame_receipt_sha256": frame_sha,
        "visual_review_receipt_sha256": review_sha,
        "visual_review_claim": "unverified_by_machine",
        "live_go": False, "ck3_started": False, "screen_acquired": False,
    }


def readiness_matches_role_frame(readiness: object, frame: object) -> bool:
    """Require the public/native frame and exact connection/PID to persist."""
    if not isinstance(readiness, Mapping) or not isinstance(frame, Mapping):
        return False
    diagnostics = frame.get("diagnostics")
    if not isinstance(diagnostics, Mapping):
        return False
    snapshot_id = readiness.get("snapshot_id")
    episode_run_id = readiness.get("episode_run_id")
    if (not isinstance(snapshot_id, str) or not snapshot_id
            or not isinstance(episode_run_id, str) or not episode_run_id):
        return False
    for key in ("revision", "native_revision", "date_raw",
                "episode_character_id"):
        value = readiness.get(key)
        if type(value) is not int or value <= 0:
            return False
    if readiness.get("paused") is not True or readiness.get("map_ready") is not True:
        return False
    for key in ("snapshot_id", "revision", "native_revision", "date_raw",
                "episode_run_id", "episode_character_id", "paused", "map_ready"):
        if readiness.get(key) != frame.get(key):
            return False
    for key in ("bridge_pid", "connection_generation"):
        value = readiness.get(key)
        if type(value) is not int or value <= 0 or value != diagnostics.get(key):
            return False
    return True


def remaining_supervisor_budget(*, elapsed_seconds: float,
                                proposed_worker_seconds: float) -> dict[str, object]:
    """Reject Popen eligibility when preflight used the cleanup reserve."""
    if (isinstance(elapsed_seconds, bool) or not isinstance(elapsed_seconds, (int, float))
            or isinstance(proposed_worker_seconds, bool)
            or not isinstance(proposed_worker_seconds, (int, float))
            or not math.isfinite(elapsed_seconds)
            or not math.isfinite(proposed_worker_seconds)
            or elapsed_seconds < 0 or proposed_worker_seconds <= 0):
        raise AdmissionError("wall-clock budget inputs malformed")
    remaining = TOTAL_WALL_SECONDS - elapsed_seconds
    allowed = max(0.0, remaining - CLEANUP_RESERVE_SECONDS)
    return {"status": "TIME_BUDGET_READY" if proposed_worker_seconds <= allowed
            else "RED_INSUFFICIENT_TIME_BUDGET",
            "remaining_seconds": remaining,
            "maximum_worker_seconds": allowed,
            "popen_eligible": proposed_worker_seconds <= allowed,
            "cleanup_reserve_seconds": CLEANUP_RESERVE_SECONDS}


def cleanup_release_eligibility(
    *, worker_pid: int, injector_pid: int, ck3_pid: int,
    complete_owned_tree_pids: list[int], post_process_pids: list[int],
    tree_capture_complete: bool, worker_exited: bool,
    native_cleanup: Mapping[str, object] | None,
) -> dict[str, object]:
    """No bus write: inspect exact child tree, including injector, for absence."""
    roots = (worker_pid, injector_pid, ck3_pid)
    valid = (all(type(pid) is int and pid > 0 for pid in roots)
             and len(set(roots)) == len(roots)
             and isinstance(complete_owned_tree_pids, list)
             and isinstance(post_process_pids, list)
             and all(type(pid) is int and pid > 0 for pid in complete_owned_tree_pids)
             and all(type(pid) is int and pid > 0 for pid in post_process_pids)
             and len(set(complete_owned_tree_pids)) == len(complete_owned_tree_pids)
             and set(roots).issubset(complete_owned_tree_pids))
    remaining = (sorted(set(complete_owned_tree_pids) & set(post_process_pids))
                 if valid else None)
    native_ok = (isinstance(native_cleanup, Mapping)
                 and native_cleanup.get("ok") is True
                 and native_cleanup.get("tree_gone") is True
                 and native_cleanup.get("driver_closed") is True)
    eligible = bool(valid and tree_capture_complete is True
                    and worker_exited is True and remaining == [] and native_ok)
    return {"status": "RELEASE_ELIGIBLE_REVIEW_ONLY" if eligible
            else "RED_CLEANUP_NOT_PROVEN",
            "owned_tree_pids": complete_owned_tree_pids if valid else None,
            "remaining_owned_pids": remaining,
            "injector_pid": injector_pid,
            "release_eligible": eligible,
            "task_bus_mutated": False}
