"""Offline refusal tests for the pure R0368 outer admission contract."""

from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
import inspect
import json
from pathlib import Path

from PIL import Image
import pytest

from xar_autoplayer import r0368_actor_army_role_outer_contract as contract


def _check(value: bool) -> None:
    if not value:
        raise AssertionError("R0368 pure outer contract failed")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _write(path: Path, value: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return contract._sha256(path)


def _go(tmp_path: Path, *, image_is_png: bool = True) -> tuple[Path, Path]:
    original = tmp_path / "steam-original.png"
    if image_is_png:
        Image.new("RGB", (8, 6), (12, 34, 56)).save(original)
    else:
        original.write_bytes(b"image-name-only")
    image_sha = contract._sha256(original)
    frame_path = tmp_path / "freshness.json"
    frame_sha = _write(frame_path, {
        "schema": "xar.war.r0368.steam-frame-freshness.v1",
        "status": "fresh", "steam_original_sha256": image_sha,
        "captured_at_utc": _now().isoformat(),
    })
    review_path = tmp_path / "visual-review.json"
    review_sha = _write(review_path, {
        "schema": "xar.war.r0368.steam-offline-visual-review.v1",
        "status": "steam_offline_fresh_reviewed", "reviewer": "fixture-reviewer",
        "steam_original_sha256": image_sha,
        "steam_frame_receipt_sha256": frame_sha,
        "reviewed_image_size": [8, 6],
        "reviewed_at_utc": _now().isoformat(),
    })
    go_path = tmp_path / "go.json"
    _write(go_path, {
        "schema": "xar.war.r0368.role-only-live-go.v1",
        "live_authorized": True,
        "round": "R0400", "screen_task_id": "r0368-test",
        "source_pair_manifest_sha256": "A" * 64,
        "prepared_manifest_sha256": "B" * 64,
        "issued_at_utc": _now().isoformat(),
        "steam_original": {"path": str(original), "sha256": image_sha},
        "steam_frame_receipt": {"path": str(frame_path), "sha256": frame_sha},
        "steam_visual_review": {"path": str(review_path), "sha256": review_sha},
    })
    return go_path, frame_path


def _inspect_go(path: Path) -> dict[str, object]:
    return contract.inspect_go_evidence(
        path, expected_round="R0400", expected_task_id="r0368-test",
        source_pair_sha256="A" * 64, prepared_sha256="B" * 64)


def test_module_has_no_launcher_or_task_bus_mutator() -> None:
    tree = ast.parse(inspect.getsource(contract))
    imports = [alias.name for node in ast.walk(tree)
               if isinstance(node, ast.Import) for alias in node.names]
    _check(not any(name in {"subprocess", "pyautogui", "os"} for name in imports))
    _check(not any(isinstance(node, ast.ImportFrom)
                   and node.module in {"native_session", "native_auto_run"}
                   for node in ast.walk(tree)))
    _check(not hasattr(contract, "collect_r0368_managed_role_once"))
    _check(not hasattr(contract, "release_screen_after_proven_cleanup"))


def test_go_bytes_decodable_but_no_machine_live_authorization(tmp_path: Path) -> None:
    go_path, _ = _go(tmp_path)
    receipt = _inspect_go(go_path)
    _check(receipt["status"] == "GO_BYTES_STRUCTURALLY_VERIFIED_ONLY")
    _check(receipt["steam_original_dimensions"] == [8, 6])
    _check(receipt["visual_review_claim"] == "unverified_by_machine")
    _check(receipt["live_go"] is False)


def test_wrong_go_and_png_suffix_without_decodable_image_refused(tmp_path: Path) -> None:
    go_path, _ = _go(tmp_path)
    with pytest.raises(contract.AdmissionError, match="GO identity"):
        contract.inspect_go_evidence(
            go_path, expected_round="R0401", expected_task_id="r0368-test",
            source_pair_sha256="A" * 64, prepared_sha256="B" * 64)
    other = tmp_path / "bad-image"
    other.mkdir()
    bad_go, _ = _go(other, image_is_png=False)
    with pytest.raises(contract.AdmissionError, match="decodable PNG"):
        _inspect_go(bad_go)


def test_expired_frame_refused_even_when_hashes_match(tmp_path: Path) -> None:
    go_path, frame_path = _go(tmp_path)
    frame = json.loads(frame_path.read_text(encoding="utf-8"))
    frame["captured_at_utc"] = (_now() - timedelta(minutes=20)).isoformat()
    frame_sha = _write(frame_path, frame)
    review_path = tmp_path / "visual-review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review["steam_frame_receipt_sha256"] = frame_sha
    review_sha = _write(review_path, review)
    go = json.loads(go_path.read_text(encoding="utf-8"))
    go["steam_frame_receipt"]["sha256"] = frame_sha
    go["steam_visual_review"]["sha256"] = review_sha
    _write(go_path, go)
    with pytest.raises(contract.AdmissionError, match="freshness"):
        _inspect_go(go_path)


def test_stale_history_is_recorded_and_active_lease_must_be_unique(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(contract, "MAIN_TASK_BUS", tmp_path)
    tasks = tmp_path / "tasks"
    _write(tasks / "r0368-test.json", {
        "schema": "codex.task_bus.v1", "task_id": "r0368-test",
        "state": "running", "resources": [contract.SCREEN_RESOURCE],
        "last_sequence": 8, "updated_at_utc": _now().isoformat(),
    })
    _write(tasks / "old.json", {
        "schema": "codex.task_bus.v1", "task_id": "old",
        "state": "running", "resources": [contract.SCREEN_RESOURCE],
        "last_sequence": 7,
        "updated_at_utc": (_now() - timedelta(days=19)).isoformat(),
    })
    receipt = contract.inspect_screen_lease(tmp_path, "r0368-test")
    _check(receipt["owner"]["last_sequence"] == 8)
    _check([row["task_id"] for row in receipt["stale_historical_tasks"]] == ["old"])
    _write(tasks / "other.json", {
        "schema": "codex.task_bus.v1", "task_id": "other",
        "state": "running", "resources": [contract.SCREEN_RESOURCE],
        "last_sequence": 9, "updated_at_utc": _now().isoformat(),
    })
    with pytest.raises(contract.AdmissionError, match="sole fresh"):
        contract.inspect_screen_lease(tmp_path, "r0368-test")


def test_prepared_or_source_mismatch_refused_before_asset_hashing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(contract, "verify_no_launch_source_pair",
        lambda **kwargs: {"candidate_manifest_sha256": "A" * 64,
                          "release_pair_manifest_sha256": "B" * 64})
    prepared_path = tmp_path / "prepared.json"
    _write(prepared_path, {
        "schema": "xar.war.r0368.role-only-prepared-source.v1",
        "status": "READY_NO_LAUNCH", "live_authorized": False,
        "ck3_launch_attempted": False,
        "state_dir": str(tmp_path / "state"),
        "profile_dir": str(tmp_path / "profile"),
        "pipe_name": "r0368-test",
        "candidate_manifest_sha256": "WRONG",
        "release_pair_manifest_sha256": "B" * 64,
        "raw_driver_sha256": contract._ASSET_SHA256["driver-state.json"],
    })
    with pytest.raises(contract.AdmissionError, match="prepared/source"):
        contract.check_source_and_prepared_bytes(
            candidate_manifest=tmp_path / "candidate.json",
            release_pair_manifest=tmp_path / "pair.json",
            checkout=tmp_path, prepared_manifest=prepared_path,
            state_dir=tmp_path / "state", profile_dir=tmp_path / "profile",
            environment_manifest=tmp_path / "environment.json",
            pipe_name="r0368-test")


def test_real_rebind_digest_shapes_match_distinct_manifest_file_hash(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = {"candidate_manifest_sha256": "A" * 64,
              "release_pair_manifest_sha256": "B" * 64}
    monkeypatch.setattr(contract, "verify_no_launch_source_pair", lambda **_: source)
    state = tmp_path / "state"
    profile = state / "profile"
    checkpoint = profile / "save games" / "xar_checkpoint.ck3"
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b"raw checkpoint fixture")
    sidecar = state / "player-child-matrilineal-formal-v1.json"
    sidecar.write_bytes(b"sidecar fixture")
    driver = state / "native-session" / "driver-state.json"
    driver.parent.mkdir(parents=True)
    driver.write_bytes(b"rebound driver fixture")
    raw_driver_sha = "D" * 64
    monkeypatch.setattr(contract, "_ASSET_SHA256", {
        "xar_checkpoint.ck3": contract._sha256(checkpoint),
        "player-child-matrilineal-formal-v1.json": contract._sha256(sidecar),
        "driver-state.json": raw_driver_sha,
    })
    environment = tmp_path / "environment.json"
    internal_binding_sha = "C" * 64
    environment_sha = _write(environment, {
        "environment_sha256": internal_binding_sha.lower(),
    })
    rebind = state / "ordinary-seed-rebind-v1.json"
    rebind_sha = _write(rebind, {
        "schema": "xar.ck3.ordinary-seed-rebind/v1", "ok": True,
        "status": "rebound", "ck3_launch_attempted": False,
        "desktop_interaction": False, "state_dir": str(state),
        "profile_dir": str(profile), "pipe_name": "r0368-test",
        "driver_state": {"source_sha256": raw_driver_sha.lower(),
                         "target_sha256": contract._sha256(driver).lower()},
        "environment": {"target_sha256": internal_binding_sha.lower()},
        "save": {"bytes_unchanged": True},
    })
    prepared = tmp_path / "prepared.json"
    _write(prepared, {
        "schema": "xar.war.r0368.role-only-prepared-source.v1",
        "status": "READY_NO_LAUNCH", "live_authorized": False,
        "ck3_launch_attempted": False, "state_dir": str(state),
        "profile_dir": str(profile), "pipe_name": "r0368-test",
        **source, "raw_driver_sha256": raw_driver_sha,
        "prepared_driver_sha256": contract._sha256(driver),
        "rebind_receipt_sha256": rebind_sha,
        "environment_sha256": environment_sha,
    })
    result = contract.check_source_and_prepared_bytes(
        candidate_manifest=tmp_path / "candidate.json",
        release_pair_manifest=tmp_path / "pair.json", checkout=tmp_path,
        prepared_manifest=prepared, state_dir=state, profile_dir=profile,
        environment_manifest=environment, pipe_name="r0368-test")
    _check(result["status"] == "PREPARED_BYTES_VERIFIED_LIVE_CLOSED")
    _check(result["live_go"] is False)
    changed_rebind = json.loads(rebind.read_text(encoding="utf-8"))
    changed_rebind["environment"]["target_sha256"] = "F" * 64
    changed_rebind_sha = _write(rebind, changed_rebind)
    changed_prepared = json.loads(prepared.read_text(encoding="utf-8"))
    changed_prepared["rebind_receipt_sha256"] = changed_rebind_sha
    _write(prepared, changed_prepared)
    with pytest.raises(contract.AdmissionError, match="official prepared rebind"):
        contract.check_source_and_prepared_bytes(
            candidate_manifest=tmp_path / "candidate.json",
            release_pair_manifest=tmp_path / "pair.json", checkout=tmp_path,
            prepared_manifest=prepared, state_dir=state, profile_dir=profile,
            environment_manifest=environment, pipe_name="r0368-test")


def _frame_pair() -> tuple[dict[str, object], dict[str, object]]:
    readiness = {
        "snapshot_id": "native:3", "revision": 4, "native_revision": 3,
        "date_raw": 53219928, "episode_run_id": "native-29829-2bc2d599f7f9",
        "episode_character_id": 29829, "paused": True, "map_ready": True,
        "bridge_pid": 901, "connection_generation": 2,
    }
    frame = {key: value for key, value in readiness.items()
             if key not in {"bridge_pid", "connection_generation"}}
    frame["diagnostics"] = {"bridge_pid": 901, "connection_generation": 2}
    return readiness, frame


def test_readiness_binds_pid_and_generation_to_role_frame() -> None:
    readiness, frame = _frame_pair()
    _check(contract.readiness_matches_role_frame(readiness, frame))
    frame["diagnostics"]["bridge_pid"] = 902
    _check(not contract.readiness_matches_role_frame(readiness, frame))
    frame["diagnostics"]["bridge_pid"] = 901
    frame["diagnostics"]["connection_generation"] = 3
    _check(not contract.readiness_matches_role_frame(readiness, frame))


@pytest.mark.parametrize("key", [
    "snapshot_id", "revision", "native_revision", "date_raw",
    "episode_run_id", "episode_character_id", "paused", "map_ready",
    "bridge_pid", "connection_generation",
])
def test_readiness_rejects_same_missing_or_null_field(key: str) -> None:
    readiness, frame = _frame_pair()
    target = frame["diagnostics"] if key in {"bridge_pid", "connection_generation"} else frame
    for value in (None,):
        readiness[key] = value
        target[key] = value
        _check(not contract.readiness_matches_role_frame(readiness, frame))
    readiness, frame = _frame_pair()
    readiness.pop(key)
    target = frame["diagnostics"] if key in {"bridge_pid", "connection_generation"} else frame
    target.pop(key)
    _check(not contract.readiness_matches_role_frame(readiness, frame))


@pytest.mark.parametrize("key,bad_value", [
    ("snapshot_id", 1), ("episode_run_id", 1),
    ("revision", "4"), ("native_revision", True),
    ("date_raw", 0), ("episode_character_id", -1),
    ("paused", 1), ("map_ready", 1),
    ("bridge_pid", "901"), ("connection_generation", 0),
])
def test_readiness_rejects_same_wrong_type_or_value(
    key: str, bad_value: object,
) -> None:
    readiness, frame = _frame_pair()
    readiness[key] = bad_value
    target = frame["diagnostics"] if key in {"bridge_pid", "connection_generation"} else frame
    target[key] = bad_value
    _check(not contract.readiness_matches_role_frame(readiness, frame))


def test_preflight_budget_reserves_cleanup_before_popen() -> None:
    enough = contract.remaining_supervisor_budget(
        elapsed_seconds=100, proposed_worker_seconds=1000)
    _check(enough["popen_eligible"] is True)
    exhausted = contract.remaining_supervisor_budget(
        elapsed_seconds=1600, proposed_worker_seconds=1)
    _check(exhausted["status"] == "RED_INSUFFICIENT_TIME_BUDGET")
    _check(exhausted["popen_eligible"] is False)
    for malformed in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(contract.AdmissionError, match="budget inputs malformed"):
            contract.remaining_supervisor_budget(
                elapsed_seconds=malformed, proposed_worker_seconds=1)
        with pytest.raises(contract.AdmissionError, match="budget inputs malformed"):
            contract.remaining_supervisor_budget(
                elapsed_seconds=1, proposed_worker_seconds=malformed)


def test_cleanup_requires_injector_and_complete_descendant_absence() -> None:
    common = {"worker_pid": 100, "injector_pid": 101, "ck3_pid": 102,
              "complete_owned_tree_pids": [100, 101, 102, 103],
              "tree_capture_complete": True, "worker_exited": True,
              "native_cleanup": {"ok": True, "tree_gone": True,
                                 "driver_closed": True}}
    missing = contract.cleanup_release_eligibility(
        **common, post_process_pids=[101])
    _check(missing["release_eligible"] is False)
    _check(missing["remaining_owned_pids"] == [101])
    clear = contract.cleanup_release_eligibility(
        **common, post_process_pids=[])
    _check(clear["release_eligible"] is True)
    _check(clear["task_bus_mutated"] is False)
    unproven = contract.cleanup_release_eligibility(
        **{**common, "tree_capture_complete": False}, post_process_pids=[])
    _check(unproven["release_eligible"] is False)
    aliased_roots = contract.cleanup_release_eligibility(
        **{**common, "injector_pid": 100}, post_process_pids=[])
    _check(aliased_roots["release_eligible"] is False)
    _check(aliased_roots["status"] == "RED_CLEANUP_NOT_PROVEN")
