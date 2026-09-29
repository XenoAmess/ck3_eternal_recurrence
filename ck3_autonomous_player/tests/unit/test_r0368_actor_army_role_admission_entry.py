"""No-launch admission entry tests; the fixture worker must never execute."""

from __future__ import annotations

import ast
import inspect
import json
from pathlib import Path
import subprocess
import sys

import pytest

from xar_autoplayer import r0368_actor_army_role_admission_entry as entry


def _check(condition: bool) -> None:
    if not condition:
        raise AssertionError("R0368 static admission invariant failed")


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, capture_output=True,
                   text=True, check=True, timeout=20)


def _fixture(tmp_path: Path) -> dict[str, object]:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    _git(checkout, "init", "-q")
    worker = checkout / entry.WORKER_RELATIVE
    worker.parent.mkdir(parents=True)
    worker.write_text("raise RuntimeError('worker was executed')\n", encoding="utf-8")
    _git(checkout, "add", "--", entry.WORKER_RELATIVE.as_posix())
    _git(checkout, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
         "commit", "-qm", "fixture-worker")
    head = entry._git(checkout, "rev-parse", "HEAD")
    go = tmp_path / "go.json"
    go_files = {
        "steam_original": tmp_path / "steam-original.png",
        "steam_frame_receipt": tmp_path / "frame.json",
        "steam_visual_review": tmp_path / "review.json",
    }
    for path in go_files.values():
        path.write_bytes(b"independent static fixture " + path.name.encode())
    go_record = {name: {"path": str(path), "sha256": entry._sha256(path)}
                 for name, path in go_files.items()}
    _write(go, go_record)
    output = tmp_path / "future-worker-output"
    intent_path = tmp_path / "intent.json"
    intent = {
        "schema": "xar.war.r0368.role-only-worker-intent.v1",
        "round_id": "R0400", "screen_task_id": "r0368-test",
        "checkout_head": head,
        "worker_script": str(worker.resolve()),
        "python_executable": str(Path(sys.executable).resolve()),
        "go_path": str(go.resolve()),
        "output_dir": str(output.resolve()),
        "proposed_worker_seconds": 1000,
        "argv": [str(Path(sys.executable).resolve()), str(worker.resolve()),
                 "--worker", "R0400", "--go", str(go.resolve()),
                 "--output", str(output.resolve())],
    }
    _write(intent_path, intent)
    candidate = tmp_path / "candidate.json"
    pair = tmp_path / "pair.json"
    raw_asset = tmp_path / "raw-save.ck3"
    raw_asset.write_bytes(b"raw source fixture")
    _write(candidate, {"files": {
        "raw-save.ck3": {"path": str(raw_asset),
                         "sha256": entry._sha256(raw_asset)}}})
    pair_assets = {}
    for name in ("dll", "injector", "ck3_executable"):
        path = tmp_path / f"{name}.bin"
        path.write_bytes(f"{name} fixture".encode())
        pair_assets[name] = {"path": str(path), "sha256": entry._sha256(path)}
    _write(pair, pair_assets)
    state = tmp_path / "state"
    profile = state / "profile"
    prepared_paths = {
        "checkpoint": profile / "save games" / "xar_checkpoint.ck3",
        "sidecar": state / "player-child-matrilineal-formal-v1.json",
        "driver": state / "native-session" / "driver-state.json",
        "rebind": state / "ordinary-seed-rebind-v1.json",
        "environment": profile / "xar-autoplayer-environment.json",
    }
    for name, path in prepared_paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(f"{name} prepared fixture".encode())
    prepared = tmp_path / "prepared.json"
    _write(prepared, {
        "state_dir": str(state),
        "profile_dir": str(profile),
        "pipe_name": "fixture-pipe",
        "candidate_manifest_sha256": entry._sha256(candidate),
    })
    return {"checkout": checkout, "worker": worker, "go": go,
            "intent_path": intent_path, "intent": intent,
            "prepared": prepared, "output": output,
            "go_record": go_record, "go_files": go_files,
            "prepared_paths": prepared_paths, "raw_asset": raw_asset,
            "pair_assets": pair_assets}


def _review(fixture: dict[str, object], tmp_path: Path,
            *, cleanup: Path | None = None) -> dict[str, object]:
    return entry.review_no_launch_admission(
        checkout=fixture["checkout"],
        candidate_manifest=tmp_path / "candidate.json",
        release_pair_manifest=tmp_path / "pair.json",
        prepared_manifest=fixture["prepared"],
        worker_intent_path=fixture["intent_path"],
        go_path=fixture["go"], cleanup_evidence_path=cleanup,
        bus_dir=tmp_path / "bus",
    )


def _stub_static_inputs(monkeypatch: pytest.MonkeyPatch,
                        fixture: dict[str, object]) -> None:
    monkeypatch.setattr(entry, "check_source_and_prepared_bytes", lambda **_: {
        "status": "PREPARED_BYTES_VERIFIED_LIVE_CLOSED",
        "source_pair_manifest_sha256": entry._sha256(
            fixture["checkout"].parent / "pair.json"),
        "prepared_manifest_sha256": entry._sha256(fixture["prepared"]),
        "prepared_hashes": {name: entry._sha256(path) for name, path in
                            fixture["prepared_paths"].items()},
    })
    monkeypatch.setattr(entry, "inspect_screen_lease", lambda *_args, **_kwargs: {
        "status": "SOLE_FRESH_OWNER_OBSERVED",
        "owner": {"task_id": "r0368-test", "last_sequence": 8,
                  "updated_at_utc": "2026-09-29T19:00:00+00:00"},
    })
    monkeypatch.setattr(entry, "inspect_go_evidence", lambda *_args, **_kwargs: {
        "status": "GO_BYTES_STRUCTURALLY_VERIFIED_ONLY",
        "go_sha256": entry._sha256(fixture["go"]),
        "steam_original_sha256": entry._sha256(
            fixture["go_files"]["steam_original"]),
        "frame_receipt_sha256": entry._sha256(
            fixture["go_files"]["steam_frame_receipt"]),
        "visual_review_receipt_sha256": entry._sha256(
            fixture["go_files"]["steam_visual_review"]),
        "visual_review_claim": "unverified_by_machine",
        "live_go": False,
    })


def test_entry_has_no_worker_launcher_or_bus_mutator() -> None:
    tree = ast.parse(inspect.getsource(entry))
    _check(not any(isinstance(node, ast.Name) and node.id == "Popen"
                   for node in ast.walk(tree)))
    _check(not any(isinstance(node, ast.Import) and any(
        alias.name in {"subprocess", "pyautogui"} for alias in node.names)
        for node in ast.walk(tree)))
    _check(not hasattr(entry, "native_session"))
    _check(not hasattr(entry, "release_screen_after_proven_cleanup"))


def test_exact_head_blob_and_argv_are_structural_only(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    receipt = entry.inspect_worker_intent(
        checkout=fixture["checkout"], intent=fixture["intent"],
        intent_path=fixture["intent_path"])
    _check(receipt["status"] == "WORKER_BLOB_AND_ARGV_VERIFIED_NO_EXECUTION")
    _check(receipt["worker_executed"] is False)
    _check(not fixture["output"].exists())


def test_missing_worker_tampered_blob_and_extra_arg_fail_closed(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    intent = fixture["intent"]
    intent["argv"].append("--unsafe")
    with pytest.raises(entry.AdmissionError, match="worker argv"):
        entry.inspect_worker_intent(
            checkout=fixture["checkout"], intent=intent,
            intent_path=fixture["intent_path"])
    intent["argv"].pop()
    fixture["worker"].write_text("print('changed')\n", encoding="utf-8")
    with pytest.raises(entry.AdmissionError, match="dirty"):
        entry.inspect_worker_intent(
            checkout=fixture["checkout"], intent=intent,
            intent_path=fixture["intent_path"])
    fixture["worker"].unlink()
    with pytest.raises(entry.AdmissionError, match="absent"):
        entry.inspect_worker_intent(
            checkout=fixture["checkout"], intent=intent,
            intent_path=fixture["intent_path"])


def test_all_structural_checks_still_keep_live_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture(tmp_path)
    _stub_static_inputs(monkeypatch, fixture)
    report = _review(fixture, tmp_path)
    _check(report["status"] == "STATIC_ONLY_LIVE_CLOSED")
    _check(report["live_go"] is False)
    _check(report["worker_launch_allowed"] is False)
    _check(report["screen_release_authorized"] is False)
    _check(report["cleanup"]["status"] == "PENDING_NO_WORKER_STARTED")
    _check(not fixture["output"].exists())


def test_budget_exhausted_before_worker_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture(tmp_path)
    _stub_static_inputs(monkeypatch, fixture)
    ticks = iter((0.0, 1700.0))
    with pytest.raises(entry.AdmissionError, match="preflight exhausted"):
        entry.review_no_launch_admission(
            checkout=fixture["checkout"],
            candidate_manifest=tmp_path / "candidate.json",
            release_pair_manifest=tmp_path / "pair.json",
            prepared_manifest=fixture["prepared"],
            worker_intent_path=fixture["intent_path"],
            go_path=fixture["go"], bus_dir=tmp_path / "bus",
            monotonic_clock=lambda: next(ticks),
        )
    _check(not fixture["output"].exists())


def test_go_and_lease_drift_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = _fixture(tmp_path)
    _stub_static_inputs(monkeypatch, fixture)
    original_go = entry.inspect_go_evidence
    def changed_go(*args: object, **kwargs: object) -> dict[str, object]:
        receipt = original_go(*args, **kwargs)
        fixture["go"].write_bytes(b"changed after GO review")
        return receipt
    monkeypatch.setattr(entry, "inspect_go_evidence", changed_go)
    with pytest.raises(entry.AdmissionError, match="GO bytes drifted"):
        _review(fixture, tmp_path)
    _write(fixture["go"], fixture["go_record"])
    _stub_static_inputs(monkeypatch, fixture)
    sequence = iter((8, 9))
    monkeypatch.setattr(entry, "inspect_screen_lease", lambda *_args, **_kwargs: {
        "owner": {"task_id": "r0368-test", "last_sequence": next(sequence)},
    })
    with pytest.raises(entry.AdmissionError, match="lease drifted"):
        _review(fixture, tmp_path)


@pytest.mark.parametrize("target_kind,expected_error", [
    ("checkpoint", "prepared asset bytes drifted"),
    ("sidecar", "prepared asset bytes drifted"),
    ("driver", "prepared asset bytes drifted"),
    ("rebind", "prepared asset bytes drifted"),
    ("environment", "prepared asset bytes drifted"),
    ("raw", "raw source or Release pair bytes drifted"),
    ("dll", "raw source or Release pair bytes drifted"),
    ("injector", "raw source or Release pair bytes drifted"),
    ("ck3_executable", "raw source or Release pair bytes drifted"),
    ("steam_original", "GO attachment bytes drifted"),
    ("steam_frame_receipt", "GO attachment bytes drifted"),
    ("steam_visual_review", "GO attachment bytes drifted"),
])
def test_attested_asset_drift_during_review_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    target_kind: str, expected_error: str,
) -> None:
    fixture = _fixture(tmp_path)
    _stub_static_inputs(monkeypatch, fixture)
    targets = {**fixture["prepared_paths"],
               **{name: tmp_path / f"{name}.bin"
                  for name in ("dll", "injector", "ck3_executable")},
               **fixture["go_files"], "raw": fixture["raw_asset"]}
    target = targets[target_kind]
    original_go = entry.inspect_go_evidence
    def change_after_initial_gate(*args: object, **kwargs: object) -> dict[str, object]:
        result = original_go(*args, **kwargs)
        target.write_bytes(b"drift after initial attestation")
        return result
    monkeypatch.setattr(entry, "inspect_go_evidence", change_after_initial_gate)
    with pytest.raises(entry.AdmissionError, match=expected_error):
        _review(fixture, tmp_path)
    _check(not fixture["output"].exists())


def test_cleanup_review_never_grants_release_and_rejects_missing_injector() -> None:
    record = {
        "schema": "xar.war.r0368.role-only-cleanup-evidence.v1",
        "round_id": "R0400", "screen_task_id": "r0368-test",
        "source_pair_manifest_sha256": "A" * 64,
        "prepared_manifest_sha256": "B" * 64,
        "go_sha256": "C" * 64, "worker_sha256": "D" * 64,
        "gameplay_actions": 0, "date_advance_actions": 0,
        "worker_pid": 100, "injector_pid": 101, "ck3_pid": 102,
        "complete_owned_tree_pids": [100, 101, 102, 103],
        "post_process_pids": [], "tree_capture_complete": True,
        "worker_exited": True,
        "native_cleanup": {"ok": True, "tree_gone": True,
                           "driver_closed": True},
    }
    kwargs = {"round_id": "R0400", "task_id": "r0368-test",
              "source_pair_sha256": "A" * 64,
              "prepared_sha256": "B" * 64, "go_sha256": "C" * 64,
              "worker_sha256": "D" * 64}
    reviewed = entry.inspect_cleanup_record(record, **kwargs)
    _check(reviewed["status"] == "CLEANUP_EVIDENCE_REVIEW_ONLY")
    _check(reviewed["screen_release_authorized"] is False)
    with pytest.raises(entry.AdmissionError, match="cleanup evidence identity"):
        entry.inspect_cleanup_record({**record, "go_sha256": "X" * 64}, **kwargs)
    with pytest.raises(entry.AdmissionError, match="full tree absence"):
        entry.inspect_cleanup_record(
            {**record, "post_process_pids": [101]}, **kwargs)
