"""Offline R0368 supervisor transcript review; never launch or release CK3.

The current runtime does not expose an injector PID and complete descendant
tree. Even a structurally valid fixture remains a live STOP until a separate
implementation and human review establish real process provenance.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Mapping

from .r0368_actor_army_role_operator import _sha256
from .r0368_actor_army_role_outer_contract import (
    AdmissionError, CLEANUP_RESERVE_SECONDS, TOTAL_WALL_SECONDS,
    cleanup_release_eligibility,
)


HEARTBEAT_MAX_GAP_SECONDS = 120.0
_SHA256_HEX = re.compile(r"[0-9a-fA-F]{64}\Z")


def _object(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise AdmissionError(f"expected JSON object: {path}")
    return value


def _positive_int(value: object) -> bool:
    return type(value) is int and value > 0


def _nonempty_text(value: object) -> bool:
    return type(value) is str and bool(value.strip())


def _sha256_text(value: object) -> bool:
    return type(value) is str and _SHA256_HEX.fullmatch(value) is not None


def _zero_int(value: object) -> bool:
    return type(value) is int and value == 0


def _seconds(value: object) -> bool:
    return (type(value) in (int, float) and value >= 0
            and value <= TOTAL_WALL_SECONDS)


def _process_tree(transcript: Mapping[str, object],
                  supervisor_pid: int) -> dict[str, object]:
    tree = transcript.get("process_tree")
    if not isinstance(tree, Mapping) or tree.get("capture_complete") is not True:
        raise AdmissionError("complete process tree capture missing")
    roots = tree.get("roots")
    rows = tree.get("processes")
    if not isinstance(roots, Mapping) or not isinstance(rows, list):
        raise AdmissionError("process tree roots or rows missing")
    root_pids: dict[str, int] = {}
    for name in ("worker", "injector", "ck3"):
        root = roots.get(name)
        if (not isinstance(root, Mapping) or not _positive_int(root.get("pid"))
                or not isinstance(root.get("creation_key"), str)
                or not root["creation_key"]):
            raise AdmissionError(f"{name} PID/creation identity missing")
        root_pids[name] = root["pid"]
    if len(set(root_pids.values())) != 3:
        raise AdmissionError("worker/injector/CK3 root PID identities overlap")
    by_pid: dict[int, Mapping[str, object]] = {}
    for row in rows:
        if (not isinstance(row, Mapping) or not _positive_int(row.get("pid"))
                or type(row.get("parent_pid")) is not int
                or not isinstance(row.get("creation_key"), str)
                or not row["creation_key"] or row["pid"] in by_pid):
            raise AdmissionError("process tree row identity malformed or duplicated")
        by_pid[row["pid"]] = row
    if (not set(root_pids.values()).issubset(by_pid)
            or by_pid[root_pids["worker"]].get("parent_pid") != supervisor_pid
            or by_pid[root_pids["injector"]].get("parent_pid") != root_pids["worker"]
            or by_pid[root_pids["ck3"]].get("parent_pid") != root_pids["worker"]):
        raise AdmissionError("process tree root parentage differs")
    for name, pid in root_pids.items():
        if by_pid[pid].get("creation_key") != roots[name]["creation_key"]:
            raise AdmissionError("process tree root creation identity differs")
    for pid, row in by_pid.items():
        if pid == root_pids["worker"]:
            continue
        seen = {pid}
        parent = row["parent_pid"]
        while parent != root_pids["worker"]:
            if parent not in by_pid or parent in seen:
                raise AdmissionError("descendant lacks an acyclic owned parent chain")
            seen.add(parent)
            parent = by_pid[parent]["parent_pid"]
    post = tree.get("post_process_pids")
    if (not isinstance(post, list)
            or any(not _positive_int(pid) for pid in post)):
        raise AdmissionError("post-process inventory missing")
    return {"roots": root_pids, "owned_pids": sorted(by_pid),
            "post_process_pids": post}


def _heartbeat_chain(transcript: Mapping[str, object], *, task_id: str,
                     go_sha256: str, initial_sequence: int,
                     worker_start: float, worker_exit: float) -> dict[str, object]:
    rows = transcript.get("heartbeats")
    if not isinstance(rows, list) or len(rows) < 2:
        raise AdmissionError("managed heartbeat chain is missing")
    prior_time = worker_start
    prior_sequence = initial_sequence
    for row in rows:
        if (not isinstance(row, Mapping)
                or row.get("screen_task_id") != task_id
                or row.get("go_sha256") != go_sha256
                or not _seconds(row.get("elapsed_seconds"))
                or type(row.get("sequence")) is not int
                or row["sequence"] <= prior_sequence
                or not worker_start <= row["elapsed_seconds"] <= worker_exit
                or row["elapsed_seconds"] - prior_time > HEARTBEAT_MAX_GAP_SECONDS):
            raise AdmissionError("heartbeat identity, sequence or deadline drifted")
        prior_time = row["elapsed_seconds"]
        prior_sequence = row["sequence"]
    if worker_exit - prior_time > HEARTBEAT_MAX_GAP_SECONDS:
        raise AdmissionError("heartbeat lapsed before worker exit")
    return {"count": len(rows), "last_sequence": prior_sequence,
            "last_elapsed_seconds": prior_time}


def _native_cleanup(transcript: Mapping[str, object], marker: Path) -> Mapping[str, object]:
    cleanup = transcript.get("native_cleanup")
    control = cleanup.get("control_files_absent") if isinstance(cleanup, Mapping) else None
    inventory = cleanup.get("final_ck3_inventory") if isinstance(cleanup, Mapping) else None
    if (not isinstance(cleanup, Mapping)
            or cleanup.get("ok") is not True
            or cleanup.get("tree_gone") is not True
            or cleanup.get("cleanup_proven") is not True
            or cleanup.get("driver_closed") is not True
            or not _zero_int(cleanup.get("job_active_processes_final"))
            or cleanup.get("watchdog_state_after") != "absent"
            or not isinstance(control, Mapping) or not control
            or any(value is not True for value in control.values())
            or control.get(str(marker)) is not True
            or not isinstance(inventory, Mapping)
            or inventory.get("processes") != []):
        raise AdmissionError("native shutdown and watchdog cleanup are unproven")
    return cleanup


def review_offline_supervisor_transcript(
    *, transcript: Mapping[str, object], admission: Mapping[str, object],
    intent: Mapping[str, object], state_dir: Path,
    stdout_path: Path, stderr_path: Path,
) -> dict[str, object]:
    """Validate an offline fixture's shape, never its real-world provenance."""
    source = admission.get("source_prepared")
    worker = admission.get("worker")
    go = admission.get("go")
    lease = admission.get("lease_after")
    spawn = transcript.get("spawn")
    owner = lease.get("owner") if isinstance(lease, Mapping) else None
    if (not isinstance(source, Mapping)
            or not isinstance(worker, Mapping)
            or not isinstance(go, Mapping)
            or not isinstance(intent, Mapping)
            or not isinstance(spawn, Mapping)
            or not all(_sha256_text(value) for value in (
                source.get("source_pair_manifest_sha256"),
                source.get("prepared_manifest_sha256"),
                worker.get("worker_sha256"), worker.get("intent_sha256"),
                go.get("go_sha256")))
            or not _nonempty_text(worker.get("round_id"))
            or not _nonempty_text(worker.get("screen_task_id"))
            or type(intent.get("argv")) is not list
            or not intent["argv"]
            or any(not _nonempty_text(arg) for arg in intent["argv"])
            or type(spawn.get("argv")) is not list
            or not spawn["argv"]
            or any(not _nonempty_text(arg) for arg in spawn["argv"])):
        raise AdmissionError("required supervisor identity or argv has invalid shape")
    if (admission.get("status") != "STATIC_ONLY_LIVE_CLOSED"
            or admission.get("live_go") is not False
            or not isinstance(source, Mapping)
            or not isinstance(worker, Mapping)
            or not isinstance(go, Mapping)
            or not isinstance(owner, Mapping)
            or transcript.get("schema")
            != "xar.war.r0368.managed-supervisor-transcript.v1"
            or transcript.get("status") != "OFFLINE_FIXTURE_ONLY"
            or transcript.get("live_authorized") is not False
            or transcript.get("round_id") != worker.get("round_id")
            or transcript.get("screen_task_id") != worker.get("screen_task_id")
            or transcript.get("source_pair_manifest_sha256")
            != source.get("source_pair_manifest_sha256")
            or transcript.get("prepared_manifest_sha256")
            != source.get("prepared_manifest_sha256")
            or transcript.get("go_sha256") != go.get("go_sha256")
            or transcript.get("worker_sha256") != worker.get("worker_sha256")
            or transcript.get("worker_intent_sha256") != worker.get("intent_sha256")
            or intent.get("round_id") != worker.get("round_id")
            or intent.get("screen_task_id") != worker.get("screen_task_id")
            or not isinstance(spawn, Mapping)
            or intent.get("argv") != spawn.get("argv")
            or owner.get("task_id") != worker.get("screen_task_id")
            or not _positive_int(owner.get("last_sequence"))
            or not _zero_int(transcript.get("gameplay_actions"))
            or not _zero_int(transcript.get("date_advance_actions"))):
        raise AdmissionError("supervisor transcript source/GO/lease identity differs")
    exit_row = transcript.get("worker_exit")
    if (not isinstance(spawn, Mapping) or not isinstance(exit_row, Mapping)
            or not _positive_int(spawn.get("supervisor_pid"))
            or not _positive_int(spawn.get("worker_pid"))
            or spawn.get("supervisor_pid") == spawn.get("worker_pid")
            or not isinstance(spawn.get("worker_creation_key"), str)
            or not spawn["worker_creation_key"]
            or spawn.get("stdin") != "DEVNULL"
            or spawn.get("stdout") != "PIPE"
            or spawn.get("stderr") != "PIPE"
            or not _seconds(spawn.get("elapsed_seconds"))
            or exit_row.get("pid") != spawn.get("worker_pid")
            or exit_row.get("creation_key") != spawn.get("worker_creation_key")
            or not _zero_int(exit_row.get("returncode"))
            or not _seconds(exit_row.get("elapsed_seconds"))):
        raise AdmissionError("worker subprocess start or exact exit is unproven")
    worker_start = spawn["elapsed_seconds"]
    worker_exit = exit_row["elapsed_seconds"]
    finish = transcript.get("cleanup_finished_elapsed_seconds")
    if (not _seconds(finish)
            or not worker_start <= worker_exit <= finish
            or worker_exit > TOTAL_WALL_SECONDS - CLEANUP_RESERVE_SECONDS):
        raise AdmissionError("worker timeout or cleanup reserve exhausted")
    heartbeats = _heartbeat_chain(
        transcript, task_id=str(worker["screen_task_id"]),
        go_sha256=str(go["go_sha256"]),
        initial_sequence=owner["last_sequence"],
        worker_start=worker_start, worker_exit=worker_exit,
    )
    tree = _process_tree(transcript, spawn["supervisor_pid"])
    if (tree["roots"]["worker"] != spawn["worker_pid"]
            or transcript["process_tree"]["roots"]["worker"]["creation_key"]
            != spawn["worker_creation_key"]):
        raise AdmissionError("spawned worker PID differs from owned tree")
    marker = (state_dir / "control" / "unsafe-cleanup.json").resolve()
    marker_row = transcript.get("unsafe_marker")
    if (not isinstance(marker_row, Mapping)
            or marker_row.get("path") != str(marker)
            or marker_row.get("existed_before") is not False
            or marker_row.get("exists_after") is not False
            or marker.exists()):
        raise AdmissionError("unsafe cleanup marker absent proof failed")
    cleanup = _native_cleanup(transcript, marker)
    reviewed = cleanup_release_eligibility(
        worker_pid=tree["roots"]["worker"],
        injector_pid=tree["roots"]["injector"],
        ck3_pid=tree["roots"]["ck3"],
        complete_owned_tree_pids=tree["owned_pids"],
        post_process_pids=tree["post_process_pids"],
        tree_capture_complete=True, worker_exited=True,
        native_cleanup=cleanup,
    )
    if reviewed["release_eligible"] is not True:
        raise AdmissionError("full worker/injector/CK3 tree absence not proven")
    outputs = transcript.get("worker_outputs")
    if (not isinstance(outputs, Mapping)
            or outputs.get("stdout_path") != str(stdout_path.resolve())
            or outputs.get("stderr_path") != str(stderr_path.resolve())
            or outputs.get("stdout_sha256") != _sha256(stdout_path)
            or outputs.get("stderr_sha256") != _sha256(stderr_path)):
        raise AdmissionError("worker stdout/stderr bytes differ")
    return {
        "schema": "xar.war.r0368.offline-supervisor-review.v1",
        "status": "OFFLINE_EVIDENCE_SHAPE_LIVE_STOP",
        "heartbeat_count": heartbeats["count"],
        "last_heartbeat_sequence": heartbeats["last_sequence"],
        "owned_process_pids": tree["owned_pids"],
        "cleanup_review": reviewed,
        "live_stop_reasons": [
            "no_real_supervisor_or_worker_execution_in_this_review",
            "runtime_does_not_expose_injector_pid_and_complete_tree_attestation",
            "self_described_transcript_is_not_process_provenance",
        ],
        "live_go": False,
        "worker_launch_allowed": False,
        "screen_release_authorized": False,
        "task_bus_mutated": False,
        "ck3_started": False,
        "gameplay_actions": 0,
        "date_advance_actions": 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="R0368 offline supervisor transcript review")
    parser.add_argument("--no-launch", action="store_true", required=True)
    parser.add_argument("--transcript", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--intent", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--stdout", type=Path, required=True)
    parser.add_argument("--stderr", type=Path, required=True)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    args.attempt_dir.mkdir(parents=True, exist_ok=False)
    try:
        report = review_offline_supervisor_transcript(
            transcript=_object(args.transcript), admission=_object(args.admission),
            intent=_object(args.intent), state_dir=args.state_dir,
            stdout_path=args.stdout, stderr_path=args.stderr,
        )
        code = 0
    except Exception as error:
        report = {
            "schema": "xar.war.r0368.offline-supervisor-review.v1",
            "status": "RED_LIVE_STOP",
            "error": f"{type(error).__name__}: {error}",
            "live_go": False, "worker_launch_allowed": False,
            "screen_release_authorized": False,
            "task_bus_mutated": False, "ck3_started": False,
        }
        code = 2
    result = args.attempt_dir / "offline-supervisor-review.json"
    result.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(result, _sha256(result), report["status"])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
