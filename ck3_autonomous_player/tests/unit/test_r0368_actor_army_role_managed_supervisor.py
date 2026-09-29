"""Offline-only R0368 supervisor and dormant-worker refusal cases."""

from __future__ import annotations

import ast
import copy
import importlib.util
import inspect
from pathlib import Path

import pytest

from xar_autoplayer import r0368_actor_army_role_managed_supervisor as managed


WORKER_PATH = Path(__file__).resolve().parents[3] / "tools" / "r0368_actor_army_role_once_enable.py"


def _check(value: bool) -> None:
    if not value:
        raise AssertionError("R0368 offline supervisor invariant failed")


def _fixture(tmp_path: Path) -> dict[str, object]:
    state = tmp_path / "state"
    marker = (state / "control" / "unsafe-cleanup.json").resolve()
    stdout = tmp_path / "worker.stdout"
    stderr = tmp_path / "worker.stderr"
    stdout.write_bytes(b"fixture stdout")
    stderr.write_bytes(b"fixture stderr")
    intent = {"round_id": "R0400", "screen_task_id": "r0368-test",
              "argv": ["python", "worker", "--worker", "R0400"]}
    admission = {
        "status": "STATIC_ONLY_LIVE_CLOSED", "live_go": False,
        "source_prepared": {"source_pair_manifest_sha256": "A" * 64,
                            "prepared_manifest_sha256": "B" * 64},
        "worker": {"round_id": "R0400", "screen_task_id": "r0368-test",
                   "worker_sha256": "C" * 64, "intent_sha256": "D" * 64},
        "go": {"go_sha256": "E" * 64},
        "lease_after": {"owner": {"task_id": "r0368-test",
                                   "last_sequence": 8}},
    }
    transcript = {
        "schema": "xar.war.r0368.managed-supervisor-transcript.v1",
        "status": "OFFLINE_FIXTURE_ONLY", "live_authorized": False,
        "round_id": "R0400", "screen_task_id": "r0368-test",
        "source_pair_manifest_sha256": "A" * 64,
        "prepared_manifest_sha256": "B" * 64,
        "worker_sha256": "C" * 64, "worker_intent_sha256": "D" * 64,
        "go_sha256": "E" * 64,
        "gameplay_actions": 0, "date_advance_actions": 0,
        "spawn": {"argv": intent["argv"], "supervisor_pid": 90,
                  "worker_pid": 100, "worker_creation_key": "worker@1",
                  "stdin": "DEVNULL",
                  "stdout": "PIPE", "stderr": "PIPE",
                  "elapsed_seconds": 0.0},
        "heartbeats": [
            {"elapsed_seconds": second, "sequence": sequence,
             "screen_task_id": "r0368-test", "go_sha256": "E" * 64}
            for second, sequence in ((1.0, 9), (60.0, 10), (119.0, 11))
        ],
        "worker_exit": {"pid": 100, "creation_key": "worker@1",
                        "returncode": 0,
                        "elapsed_seconds": 120.0},
        "cleanup_finished_elapsed_seconds": 130.0,
        "process_tree": {
            "capture_complete": True,
            "roots": {"worker": {"pid": 100, "creation_key": "worker@1"},
                      "injector": {"pid": 101, "creation_key": "injector@2"},
                      "ck3": {"pid": 102, "creation_key": "ck3@3"}},
            "processes": [
                {"pid": 100, "parent_pid": 90, "creation_key": "worker@1"},
                {"pid": 101, "parent_pid": 100, "creation_key": "injector@2"},
                {"pid": 102, "parent_pid": 100, "creation_key": "ck3@3"},
                {"pid": 103, "parent_pid": 102, "creation_key": "child@4"},
            ],
            "post_process_pids": [],
        },
        "unsafe_marker": {"path": str(marker), "existed_before": False,
                          "exists_after": False},
        "native_cleanup": {
            "ok": True, "tree_gone": True, "cleanup_proven": True,
            "driver_closed": True, "job_active_processes_final": 0,
            "watchdog_state_after": "absent",
            "control_files_absent": {str(marker): True,
                                     str(state / "control" / "ck3.pid"): True},
            "final_ck3_inventory": {"processes": []},
        },
        "worker_outputs": {"stdout_path": str(stdout.resolve()),
                           "stderr_path": str(stderr.resolve()),
                           "stdout_sha256": managed._sha256(stdout),
                           "stderr_sha256": managed._sha256(stderr)},
    }
    return {"transcript": transcript, "admission": admission,
            "intent": intent, "state": state, "marker": marker,
            "stdout": stdout, "stderr": stderr}


def _review(fixture: dict[str, object]) -> dict[str, object]:
    return managed.review_offline_supervisor_transcript(
        transcript=fixture["transcript"], admission=fixture["admission"],
        intent=fixture["intent"], state_dir=fixture["state"],
        stdout_path=fixture["stdout"], stderr_path=fixture["stderr"],
    )


def test_no_launch_modules_have_no_process_or_bus_write_path() -> None:
    for source in (inspect.getsource(managed), WORKER_PATH.read_text(encoding="utf-8")):
        tree = ast.parse(source)
        imports = [alias.name for node in ast.walk(tree)
                   if isinstance(node, ast.Import) for alias in node.names]
        _check("subprocess" not in imports)
        _check("pyautogui" not in imports)
        _check(not any(isinstance(node, ast.Name) and node.id == "Popen"
                       for node in ast.walk(tree)))
    _check("native_session" not in managed.__dict__)


def test_worker_live_invocation_refuses_before_output(tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location("r0368_dormant_worker", WORKER_PATH)
    _check(spec is not None and spec.loader is not None)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    go = tmp_path / "go-absent.json"
    output = tmp_path / "output-absent"
    _check(module.main(["--worker", "R0400", "--go", str(go),
                        "--output", str(output)]) == 2)
    _check(not go.exists() and not output.exists())
    report = tmp_path / "worker-no-launch.json"
    _check(module.main(["--no-launch", "--report", str(report)]) == 0)
    _check(report.is_file())
    _check(module.no_launch_report()["worker_live_authorized"] is False)


def test_complete_fixture_is_shape_only_and_never_releases(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    result = _review(fixture)
    _check(result["status"] == "OFFLINE_EVIDENCE_SHAPE_LIVE_STOP")
    _check(result["live_go"] is False)
    _check(result["screen_release_authorized"] is False)
    _check(result["task_bus_mutated"] is False)
    _check(result["cleanup_review"]["release_eligible"] is True)
    _check("runtime_does_not_expose_injector_pid_and_complete_tree_attestation"
           in result["live_stop_reasons"])


_SHA_IDENTITIES = ("source_pair_manifest_sha256", "prepared_manifest_sha256",
                   "worker_sha256", "intent_sha256", "go_sha256")
_ALL_IDENTITIES = _SHA_IDENTITIES + ("round_id", "screen_task_id")


@pytest.mark.parametrize("identity,bad", [
    (identity, bad)
    for identity in _ALL_IDENTITIES
    for bad in ("missing", None, "", " ", 42)
] + [(identity, "G" * 64) for identity in _SHA_IDENTITIES])
def test_matching_invalid_identity_is_refused(
    tmp_path: Path, identity: str, bad: object,
) -> None:
    fixture = _fixture(tmp_path)
    admission = fixture["admission"]
    transcript = fixture["transcript"]
    intent = fixture["intent"]
    if identity in ("source_pair_manifest_sha256", "prepared_manifest_sha256"):
        source = admission["source_prepared"]
        transcript_key = identity
    elif identity == "go_sha256":
        source = admission["go"]
        transcript_key = identity
    else:
        source = admission["worker"]
        transcript_key = ("worker_intent_sha256" if identity == "intent_sha256"
                          else identity)
    for row, key in ((source, identity), (transcript, transcript_key)):
        if bad == "missing":
            row.pop(key)
        else:
            row[key] = bad
    if identity in ("round_id", "screen_task_id"):
        if bad == "missing":
            intent.pop(identity)
        else:
            intent[identity] = bad
    with pytest.raises(managed.AdmissionError, match="required supervisor identity"):
        _review(fixture)


@pytest.mark.parametrize("bad", ["missing", None, [], [""], ["python", None],
                                      ("python", "worker"), "python worker"])
def test_matching_invalid_argv_is_refused(tmp_path: Path, bad: object) -> None:
    fixture = _fixture(tmp_path)
    for row in (fixture["intent"], fixture["transcript"]["spawn"]):
        if bad == "missing":
            row.pop("argv")
        else:
            row["argv"] = bad
    with pytest.raises(managed.AdmissionError, match="required supervisor identity"):
        _review(fixture)


@pytest.mark.parametrize("field,error", [
    ("gameplay_actions", "source/GO/lease identity"),
    ("date_advance_actions", "source/GO/lease identity"),
    ("returncode", "exact exit"),
    ("job_active_processes_final", "native shutdown"),
])
@pytest.mark.parametrize("bad", [False, 0.0, "0", None])
def test_zero_counts_require_exact_int(
    tmp_path: Path, field: str, error: str, bad: object,
) -> None:
    fixture = _fixture(tmp_path)
    transcript = fixture["transcript"]
    if field == "returncode":
        row = transcript["worker_exit"]
    elif field == "job_active_processes_final":
        row = transcript["native_cleanup"]
    else:
        row = transcript
    row[field] = bad
    with pytest.raises(managed.AdmissionError, match=error):
        _review(fixture)


@pytest.mark.parametrize("mutation,message", [
    ("go_drift", "source/GO/lease identity"),
    ("worker_failure", "exact exit"),
    ("worker_creation_drift", "exact exit"),
    ("worker_timeout", "timeout or cleanup reserve"),
    ("cleanup_timeout", "timeout or cleanup reserve"),
    ("heartbeat_gap", "heartbeat identity, sequence or deadline"),
    ("heartbeat_sequence", "heartbeat identity, sequence or deadline"),
    ("missing_injector", "injector PID/creation identity"),
    ("duplicate_root", "root PID identities overlap"),
    ("orphan_descendant", "acyclic owned parent chain"),
    ("remaining_injector", "full worker/injector/CK3 tree absence"),
    ("native_cleanup_false", "native shutdown and watchdog cleanup"),
    ("stdout_drift", "worker stdout/stderr bytes differ"),
])
def test_failure_timeout_and_drift_are_refused(
    tmp_path: Path, mutation: str, message: str,
) -> None:
    fixture = _fixture(tmp_path)
    row = fixture["transcript"]
    if mutation == "go_drift":
        row["go_sha256"] = "F" * 64
    elif mutation == "worker_failure":
        row["worker_exit"]["returncode"] = 1
    elif mutation == "worker_creation_drift":
        row["worker_exit"]["creation_key"] = "reused-pid"
    elif mutation == "worker_timeout":
        row["worker_exit"]["elapsed_seconds"] = 1600.0
        row["cleanup_finished_elapsed_seconds"] = 1700.0
    elif mutation == "cleanup_timeout":
        row["cleanup_finished_elapsed_seconds"] = 1810.0
    elif mutation == "heartbeat_gap":
        row["heartbeats"][1]["elapsed_seconds"] = 130.0
    elif mutation == "heartbeat_sequence":
        row["heartbeats"][1]["sequence"] = 9
    elif mutation == "missing_injector":
        del row["process_tree"]["roots"]["injector"]
    elif mutation == "duplicate_root":
        row["process_tree"]["roots"]["injector"]["pid"] = 100
    elif mutation == "orphan_descendant":
        row["process_tree"]["processes"][3]["parent_pid"] = 999
    elif mutation == "remaining_injector":
        row["process_tree"]["post_process_pids"] = [101]
    elif mutation == "native_cleanup_false":
        row["native_cleanup"]["cleanup_proven"] = False
    elif mutation == "stdout_drift":
        fixture["stdout"].write_bytes(b"changed after reported SHA")
    with pytest.raises(managed.AdmissionError, match=message):
        _review(fixture)


def test_unsafe_marker_actual_file_or_claim_blocks_shape_pass(tmp_path: Path) -> None:
    fixture = _fixture(tmp_path)
    fixture["marker"].parent.mkdir(parents=True)
    fixture["marker"].write_text("unsafe", encoding="utf-8")
    with pytest.raises(managed.AdmissionError, match="unsafe cleanup marker"):
        _review(fixture)
    fixture["marker"].unlink()
    changed = copy.deepcopy(fixture["transcript"])
    changed["unsafe_marker"]["exists_after"] = True
    fixture["transcript"] = changed
    with pytest.raises(managed.AdmissionError, match="unsafe cleanup marker"):
        _review(fixture)
