"""Read-only R0368 managed-entry review. This module cannot start a worker."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import time
from typing import Mapping

from .r0368_actor_army_role_operator import _git, _sha256
from .r0368_actor_army_role_outer_contract import (
    AdmissionError, MAIN_TASK_BUS, check_source_and_prepared_bytes,
    cleanup_release_eligibility, inspect_go_evidence, inspect_screen_lease,
    remaining_supervisor_budget,
)


WORKER_RELATIVE = Path("tools/r0368_actor_army_role_once_enable.py")
_ROUND = re.compile(r"R[0-9]{4,}")


def _object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise AdmissionError(f"expected JSON object: {path}")
    return value


def _rehash_attested_rows(rows: object) -> bool:
    if not isinstance(rows, Mapping) or not rows:
        return False
    for row in rows.values():
        if (not isinstance(row, Mapping)
                or not isinstance(row.get("path"), str)
                or not isinstance(row.get("sha256"), str)
                or _sha256(Path(row["path"])) != row["sha256"].upper()):
            return False
    return True


def inspect_worker_intent(
    *, checkout: Path, intent: Mapping[str, object], intent_path: Path,
) -> dict[str, object]:
    """Compare exact proposed argv and worker bytes with the current HEAD blob."""
    root = checkout.resolve()
    worker = (root / WORKER_RELATIVE).resolve()
    try:
        worker.relative_to(root)
    except ValueError as error:
        raise AdmissionError("worker path escapes checkout") from error
    if not worker.is_file():
        raise AdmissionError("reviewed worker blob is absent from checkout")
    head = _git(root, "rev-parse", "HEAD")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise AdmissionError("worker checkout is dirty")
    committed_blob = _git(root, "rev-parse", "--verify",
                          f"{head}:{WORKER_RELATIVE.as_posix()}")
    file_blob = _git(root, "hash-object", "--", str(worker))
    if file_blob != committed_blob:
        raise AdmissionError("worker bytes differ from HEAD blob")
    round_id = intent.get("round_id")
    task_id = intent.get("screen_task_id")
    go = intent.get("go_path")
    output = intent.get("output_dir")
    python = intent.get("python_executable")
    if (intent.get("schema") != "xar.war.r0368.role-only-worker-intent.v1"
            or not isinstance(round_id, str) or _ROUND.fullmatch(round_id) is None
            or not isinstance(task_id, str) or not task_id
            or not isinstance(go, str) or not Path(go).is_absolute()
            or not isinstance(output, str) or not Path(output).is_absolute()
            or not isinstance(python, str) or not Path(python).is_absolute()
            or Path(python).resolve() != Path(sys.executable).resolve()
            or intent.get("checkout_head") != head
            or intent.get("worker_script") != str(worker)
            or Path(output).exists()):
        raise AdmissionError("worker intent identity or destination differs")
    expected_argv = [str(Path(sys.executable).resolve()), str(worker),
                     "--worker", round_id, "--go", str(Path(go).resolve()),
                     "--output", str(Path(output).resolve())]
    if intent.get("argv") != expected_argv:
        raise AdmissionError("worker argv differs from exact reviewed intent")
    return {
        "status": "WORKER_BLOB_AND_ARGV_VERIFIED_NO_EXECUTION",
        "checkout_head": head,
        "worker_relative": WORKER_RELATIVE.as_posix(),
        "worker_git_blob": committed_blob,
        "worker_sha256": _sha256(worker),
        "intent_sha256": _sha256(intent_path),
        "round_id": round_id,
        "screen_task_id": task_id,
        "go_path": str(Path(go).resolve()),
        "output_dir": str(Path(output).resolve()),
        "worker_executed": False,
    }


def inspect_cleanup_record(
    record: Mapping[str, object], *, round_id: str, task_id: str,
    source_pair_sha256: str, prepared_sha256: str, go_sha256: str,
    worker_sha256: str,
) -> dict[str, object]:
    """Review claimed post-run inventory; never release a resource."""
    if (record.get("schema") != "xar.war.r0368.role-only-cleanup-evidence.v1"
            or record.get("round_id") != round_id
            or record.get("screen_task_id") != task_id
            or record.get("source_pair_manifest_sha256") != source_pair_sha256
            or record.get("prepared_manifest_sha256") != prepared_sha256
            or record.get("go_sha256") != go_sha256
            or record.get("worker_sha256") != worker_sha256
            or record.get("gameplay_actions") != 0
            or record.get("date_advance_actions") != 0):
        raise AdmissionError("cleanup evidence identity differs")
    reviewed = cleanup_release_eligibility(
        worker_pid=record.get("worker_pid"),
        injector_pid=record.get("injector_pid"),
        ck3_pid=record.get("ck3_pid"),
        complete_owned_tree_pids=record.get("complete_owned_tree_pids"),
        post_process_pids=record.get("post_process_pids"),
        tree_capture_complete=record.get("tree_capture_complete"),
        worker_exited=record.get("worker_exited"),
        native_cleanup=record.get("native_cleanup"),
    )
    if reviewed["release_eligible"] is not True:
        raise AdmissionError("cleanup evidence does not prove full tree absence")
    return {**reviewed, "status": "CLEANUP_EVIDENCE_REVIEW_ONLY",
            "screen_release_authorized": False, "task_bus_mutated": False}


def review_no_launch_admission(
    *, checkout: Path, candidate_manifest: Path, release_pair_manifest: Path,
    prepared_manifest: Path, worker_intent_path: Path, go_path: Path,
    cleanup_evidence_path: Path | None = None,
    bus_dir: Path = MAIN_TASK_BUS,
    monotonic_clock: object = time.monotonic,
) -> dict[str, object]:
    """Run static gates only; even a full pass keeps live authorization closed."""
    clock = monotonic_clock
    if not callable(clock):
        raise AdmissionError("monotonic clock is unavailable")
    started = clock()
    prepared = _object(prepared_manifest)
    state = Path(str(prepared.get("state_dir")))
    profile = Path(str(prepared.get("profile_dir")))
    source = check_source_and_prepared_bytes(
        candidate_manifest=candidate_manifest,
        release_pair_manifest=release_pair_manifest,
        checkout=checkout, prepared_manifest=prepared_manifest,
        state_dir=state, profile_dir=profile,
        environment_manifest=profile / "xar-autoplayer-environment.json",
        pipe_name=str(prepared.get("pipe_name")),
    )
    intent = _object(worker_intent_path)
    worker = inspect_worker_intent(
        checkout=checkout, intent=intent, intent_path=worker_intent_path,
    )
    if Path(str(intent["go_path"])).resolve() != go_path.resolve():
        raise AdmissionError("GO path differs from worker argv")
    lease_before = inspect_screen_lease(bus_dir, str(intent["screen_task_id"]))
    go = inspect_go_evidence(
        go_path, expected_round=str(intent["round_id"]),
        expected_task_id=str(intent["screen_task_id"]),
        source_pair_sha256=str(source["source_pair_manifest_sha256"]),
        prepared_sha256=str(source["prepared_manifest_sha256"]),
    )
    cleanup: dict[str, object] = {
        "status": "PENDING_NO_WORKER_STARTED",
        "release_eligible": False, "task_bus_mutated": False,
    }
    if cleanup_evidence_path is not None:
        cleanup = inspect_cleanup_record(
            _object(cleanup_evidence_path),
            round_id=str(intent["round_id"]),
            task_id=str(intent["screen_task_id"]),
            source_pair_sha256=str(source["source_pair_manifest_sha256"]),
            prepared_sha256=str(source["prepared_manifest_sha256"]),
            go_sha256=str(go["go_sha256"]),
            worker_sha256=str(worker["worker_sha256"]),
        )
    if _sha256(go_path) != go["go_sha256"]:
        raise AdmissionError("GO bytes drifted during admission review")
    lease_after = inspect_screen_lease(bus_dir, str(intent["screen_task_id"]))
    if lease_before["owner"] != lease_after["owner"]:
        raise AdmissionError("screen lease drifted during admission review")
    if _git(checkout.resolve(), "rev-parse", "HEAD") != worker["checkout_head"]:
        raise AdmissionError("checkout HEAD drifted during admission review")
    if (worker["intent_sha256"] != _sha256(worker_intent_path)
            or worker["worker_sha256"]
            != _sha256(checkout / WORKER_RELATIVE)
            or source["prepared_manifest_sha256"] != _sha256(prepared_manifest)
            or source["source_pair_manifest_sha256"]
            != _sha256(release_pair_manifest)
            or prepared.get("candidate_manifest_sha256")
            != _sha256(candidate_manifest)):
        raise AdmissionError("source or worker evidence drifted during admission review")
    prepared_paths = {
        "checkpoint": profile / "save games" / "xar_checkpoint.ck3",
        "sidecar": state / "player-child-matrilineal-formal-v1.json",
        "driver": state / "native-session" / "driver-state.json",
        "rebind": state / "ordinary-seed-rebind-v1.json",
        "environment": profile / "xar-autoplayer-environment.json",
    }
    prepared_hashes = source.get("prepared_hashes")
    if (not isinstance(prepared_hashes, Mapping)
            or any(not isinstance(prepared_hashes.get(name), str)
                   or prepared_hashes[name] != _sha256(path)
                   for name, path in prepared_paths.items())):
        raise AdmissionError("prepared asset bytes drifted during admission review")
    candidate_rows = _object(candidate_manifest).get("files")
    pair_record = _object(release_pair_manifest)
    if (not _rehash_attested_rows(candidate_rows)
            or not _rehash_attested_rows({
                name: pair_record.get(name)
                for name in ("dll", "injector", "ck3_executable")
            })):
        raise AdmissionError("raw source or Release pair bytes drifted during admission review")
    go_record = _object(go_path)
    go_files = {
        "steam_original": "steam_original_sha256",
        "steam_frame_receipt": "frame_receipt_sha256",
        "steam_visual_review": "visual_review_receipt_sha256",
    }
    for row_name, digest_name in go_files.items():
        row = go_record.get(row_name)
        if (not isinstance(row, dict) or not isinstance(row.get("path"), str)
                or not isinstance(go.get(digest_name), str)
                or _sha256(Path(row["path"])) != go[digest_name]):
            raise AdmissionError("GO attachment bytes drifted during admission review")
    budget = remaining_supervisor_budget(
        elapsed_seconds=clock() - started,
        proposed_worker_seconds=intent.get("proposed_worker_seconds"),
    )
    if budget["popen_eligible"] is not True:
        raise AdmissionError("preflight exhausted the 1800s supervised budget")
    return {
        "schema": "xar.war.r0368.role-only-static-admission.v1",
        "status": "STATIC_ONLY_LIVE_CLOSED",
        "reviewed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_prepared": source, "worker": worker, "go": go,
        "lease_before": lease_before, "lease_after": lease_after,
        "budget": budget, "cleanup": cleanup,
        "human_steam_visual_review": "unverified_by_machine",
        "worker_launch_allowed": False,
        "screen_release_authorized": False,
        "live_go": False,
        "ck3_started": False,
        "worker_executed": False,
        "task_bus_mutated": False,
        "gameplay_actions": 0,
        "date_advance_actions": 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="R0368 static managed-entry review")
    parser.add_argument("--no-launch", action="store_true", required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--release-pair-manifest", type=Path, required=True)
    parser.add_argument("--prepared-manifest", type=Path, required=True)
    parser.add_argument("--worker-intent", type=Path, required=True)
    parser.add_argument("--go", type=Path, required=True)
    parser.add_argument("--cleanup-evidence", type=Path)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    args.attempt_dir.mkdir(parents=True, exist_ok=False)
    try:
        report = review_no_launch_admission(
            checkout=args.checkout,
            candidate_manifest=args.candidate_manifest,
            release_pair_manifest=args.release_pair_manifest,
            prepared_manifest=args.prepared_manifest,
            worker_intent_path=args.worker_intent, go_path=args.go,
            cleanup_evidence_path=args.cleanup_evidence,
        )
        code = 0
    except Exception as error:
        report = {
            "schema": "xar.war.r0368.role-only-static-admission.v1",
            "status": "RED_LIVE_CLOSED",
            "error": f"{type(error).__name__}: {error}",
            "worker_launch_allowed": False,
            "screen_release_authorized": False,
            "live_go": False,
            "ck3_started": False,
            "worker_executed": False,
            "task_bus_mutated": False,
            "gameplay_actions": 0,
            "date_advance_actions": 0,
        }
        code = 2
    report_path = args.attempt_dir / "admission-review.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(report_path, _sha256(report_path), report["status"])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
