"""Recording-only custody; borrowed Game and publisher are never stopped."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Callable, Literal, Never, Protocol, runtime_checkable
from uuid import UUID

Json = None | bool | int | float | str | list["Json"] | dict[str, "Json"]
Obj = dict[str, Json]
SCHEMA = "xar.recording-only-owner-admission/v1"


def need(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError(why)


def obj(value: object) -> Obj:
    need(isinstance(value, dict), "object required")
    if not isinstance(value, dict):
        raise ValueError("object required")
    return {text(k): json_value(v) for k, v in value.items()}


def json_value(value: object) -> Json:
    if value is None or type(value) in (bool, int, float, str):
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
    if isinstance(value, list):
        return [json_value(v) for v in value]
    return obj(value)


def text(value: object) -> str:
    need(type(value) is str and bool(value), "nonempty exact string required")
    if not isinstance(value, str):
        raise ValueError("string required")
    return value


def integer(value: object, low: int = 0, high: int = 0xffffffff) -> int:
    need(type(value) is int, "exact integer required")
    if not isinstance(value, int):
        raise ValueError("integer required")
    need(low <= value <= high, "integer range")
    return value


def u64(value: object) -> str:
    result = text(value)
    need(result.isascii() and result.isdecimal() and str(int(result)) == result
         and 0 < int(result) <= 0xffffffffffffffff, "canonical uint64 string")
    return result


def stamp(value: object) -> datetime:
    result = datetime.fromisoformat(text(value).replace("Z", "+00:00"))
    need(result.tzinfo is not None, "UTC offset required")
    return result.astimezone(timezone.utc)


@dataclass(frozen=True)
class RefV1:
    path: str
    bytes: int
    sha256: str

    def wire(self) -> Obj:
        return {"path": self.path, "bytes": self.bytes, "sha256": self.sha256}


def ref(value: object) -> RefV1:
    row = obj(value)
    need(set(row) == {"path", "bytes", "sha256"}, "exact ref fields")
    digest = text(row["sha256"])
    need(len(digest) == 64 and all(c in "0123456789abcdef" for c in digest),
         "lowercase SHA256")
    path = text(row["path"])
    need(Path(path).is_absolute(), "absolute source path")
    return RefV1(path, integer(row["bytes"], 1, 1048576), digest)


@dataclass(frozen=True)
class ProcessV1:
    pid: int
    birth: str
    image: str

    def wire(self) -> Obj:
        return {"pid": self.pid, "creation_filetime": self.birth,
                "executable": self.image}


def process(value: object) -> ProcessV1:
    row = obj(value)
    need(set(row) == {"pid", "creation_filetime", "executable"},
         "exact process fields")
    image = text(row["executable"])
    need(Path(image).is_absolute(), "absolute image")
    return ProcessV1(integer(row["pid"], 1), u64(row["creation_filetime"]), image)


EvidenceRoleV1 = Literal[
    "controller", "capture", "publisher_api", "launch", "placement", "profile",
    "publisher_started", "old_profile", "old_job", "old_failed",
    "old_obs_launch", "old_obs_closed", "old_closed_state"]
EvidenceV1 = dict[EvidenceRoleV1, RefV1]
EVIDENCE_ROLES = frozenset((
    "controller", "capture", "publisher_api", "launch", "placement", "profile",
    "publisher_started", "old_profile", "old_job", "old_failed",
    "old_obs_launch", "old_obs_closed", "old_closed_state"))
OutputRoleV1 = Literal["intent", "archived", "started", "closed"]
OutputsV1 = dict[OutputRoleV1, str]
OUTPUT_ROLES = frozenset(("intent", "archived", "started", "closed"))


@dataclass(frozen=True)
class RotationV1:
    before: RefV1
    archive: str


@dataclass(frozen=True)
class RecordingOnlyAdmissionV1:
    machine_id: str
    admission_id: str
    runtime_root: Path
    attempt_root: Path
    recording_root: Path
    game: ProcessV1
    publisher: ProcessV1
    old_worker: ProcessV1
    old_obs: ProcessV1
    old_session_id: str
    generation: str
    ffprobe: Path
    review_at: datetime
    evidence: EvidenceV1
    requested: RotationV1
    current: RotationV1
    outputs: OutputsV1

    def wire(self) -> Obj:
        return {"schema": SCHEMA, "machine_id": self.machine_id,
            "admission_id": self.admission_id, "root_direct_execution_release": True,
            "runtime_root": str(self.runtime_root), "attempt_root": str(self.attempt_root),
            "recording_root": str(self.recording_root), "game": self.game.wire(),
            "publisher": self.publisher.wire(), "old_worker": self.old_worker.wire(),
            "old_obs": self.old_obs.wire(), "old_session_id": self.old_session_id,
            "generation": self.generation, "ffprobe": str(self.ffprobe),
            "review_at_utc": self.review_at.isoformat(),
            "evidence": {k: v.wire() for k, v in self.evidence.items()},
            "requested": {"before": self.requested.before.wire(), "archive": self.requested.archive},
            "current": {"before": self.current.before.wire(), "archive": self.current.archive},
            "outputs": {k: v for k, v in self.outputs.items()}}


def parse_recording_only_admission_v1(value: object) -> RecordingOnlyAdmissionV1:
    row = obj(value)
    expected = {"schema", "machine_id", "admission_id", "runtime_root", "attempt_root",
                "recording_root", "game", "publisher", "old_worker", "old_obs",
                "old_session_id", "generation", "ffprobe", "review_at_utc", "evidence",
                "requested", "current", "outputs", "root_direct_execution_release"}
    need(set(row) == expected and row["schema"] == SCHEMA
         and row["root_direct_execution_release"] is True, "explicit exact admission")
    identity = str(UUID(text(row["admission_id"])))
    need(identity == row["admission_id"], "canonical admission UUID")
    sid = str(UUID(text(row["old_session_id"])))
    need(sid == row["old_session_id"], "canonical old UUID")
    roots = tuple(Path(text(row[k])) for k in ("runtime_root", "attempt_root", "recording_root"))
    need(all(p.is_absolute() for p in roots), "absolute roots")
    runtime, attempt, recording = roots
    need(attempt != runtime and recording == runtime / "recordings", "independent attempt/root")
    evidence = obj(row["evidence"])
    need(set(evidence) == EVIDENCE_ROLES, "exact evidence roles")
    refs: EvidenceV1 = {
        "controller": ref(evidence["controller"]),
        "old_profile": ref(evidence["old_profile"]),
        "capture": ref(evidence["capture"]), "publisher_api": ref(evidence["publisher_api"]),
        "launch": ref(evidence["launch"]), "placement": ref(evidence["placement"]),
        "profile": ref(evidence["profile"]), "publisher_started": ref(evidence["publisher_started"]),
        "old_job": ref(evidence["old_job"]), "old_failed": ref(evidence["old_failed"]),
        "old_obs_launch": ref(evidence["old_obs_launch"]),
        "old_obs_closed": ref(evidence["old_obs_closed"]),
        "old_closed_state": ref(evidence["old_closed_state"])}
    old_root = recording / sid
    need(Path(refs["old_job"].path) == old_root / "job.json"
         and Path(refs["old_failed"].path) == old_root / "failed.json"
         and Path(refs["old_obs_launch"].path) == old_root / "obs-launch.json",
         "old evidence stays under its original SID")
    def rotation(key: str, filename: str) -> RotationV1:
        data = obj(row[key])
        need(set(data) == {"before", "archive"}, "exact rotation")
        before, archive = ref(data["before"]), Path(text(data["archive"]))
        need(Path(before.path) == runtime / filename and archive.parent == attempt
             and archive.name not in ("", ".", ".."), "explicit canonical/archive paths")
        return RotationV1(before, str(archive))
    requested = rotation("requested", "ROOT-OBS-RECORDING-REQUESTED-C23.json")
    current = rotation("current", "ROOT-CURRENT-OBS-RECORDING-REQUESTED-C23.json")
    output = obj(row["outputs"])
    need(set(output) == OUTPUT_ROLES, "exact output roles")
    outputs: OutputsV1 = {  # One bounded independent metadata namespace.
        "intent": text(output["intent"]), "archived": text(output["archived"]),
        "started": text(output["started"]), "closed": text(output["closed"])}
    paths = [requested.archive, current.archive, *outputs.values()]
    need(len(set(paths)) == len(paths) and all(Path(p).parent == attempt for p in paths),
         "unique direct attempt leaves")
    probe = Path(text(row["ffprobe"]))
    need(probe.is_absolute() and probe.name.casefold() == "ffprobe.exe", "existing ffprobe")
    return RecordingOnlyAdmissionV1(
        text(row["machine_id"]), identity, runtime, attempt, recording,
        process(row["game"]), process(row["publisher"]), process(row["old_worker"]),
        process(row["old_obs"]), sid, text(row["generation"]), probe,
        stamp(row["review_at_utc"]), refs, requested, current, outputs)


@dataclass(frozen=True)
class WorkerRequestV1:
    session_id: str
    worker: ProcessV1
    root: Path
    legacy_request: Obj


def parse_worker_request_v1(value: object, admission: RecordingOnlyAdmissionV1) -> WorkerRequestV1:
    row = obj(value)
    need(set(row) == {"schema", "session_id", "worker_pid", "worker_creation_filetime",
                     "worker_executable", "receipt_root", "state", "runtime_qualified"},
         "exact existing capture wire")
    sid = str(UUID(text(row["session_id"])))
    need(sid == row["session_id"] and sid != admission.old_session_id
         and row["schema"] == "xar.ck3.obs-window-capture.v3"
         and row["state"] == "requested" and row["runtime_qualified"] is False,
         "actual new unqualified recording")
    birth = str(integer(row["worker_creation_filetime"], 1, 0xffffffffffffffff))
    worker = ProcessV1(integer(row["worker_pid"], 1), birth, text(row["worker_executable"]))
    need(Path(worker.image).is_absolute(), "worker image")
    need(worker.pid not in {admission.game.pid, admission.publisher.pid, admission.old_obs.pid}
         and worker != admission.old_worker, "new worker is not borrowed/old generation")
    root = Path(text(row["receipt_root"]))
    need(root == admission.recording_root / sid, "actual new SID root")
    return WorkerRequestV1(sid, worker, root, row)


class CaptureV1(Protocol):
    @property
    def __file__(self) -> str: ...
    def decision_publisher_api(self) -> object: ...
    def validate_profile(self, value: object) -> object: ...
    def _generation_helpers(self) -> object: ...
    def launch_recording(self, profile_path: Path, recording_root: Path, pid: int,
                         hwnd: int, seconds: None, *, launch_receipt: Path, ffprobe: Path,
                         placement_receipt: Path, decision_publisher_receipt: Path,
                         continuous: Literal[True]) -> object: ...
    def read_capture_closed_receipt(self, receipt_root: Path, *, session_id: str,
                                   game_pid: int, game_creation_filetime: int,
                                   recording_worker_pid: int, recording_root: Path) -> object: ...


class PublisherV1(Protocol):
    @property
    def __file__(self) -> str: ...
    def read_text_binding(self, reference: Obj, *, game: Obj) -> object: ...


class WorkerLeaseV1(Protocol):
    def wait_exit(self) -> int: ...
    def close(self) -> None: ...


class ResourcesV1(Protocol):
    """Frozen owner adapter uses actual kernel generations and ordinary exact FS."""
    machine_id: str
    def exact(self, reference: RefV1) -> bytes: ...
    def absent(self, path: str) -> bool: ...
    def write_new(self, path: str, value: Obj) -> None: ...
    def rename_exact(self, before: RefV1, archive: str) -> tuple[RefV1, str, str]: ...
    def require_live(self, identity: ProcessV1) -> None: ...
    def retain_worker(self, identity: ProcessV1) -> WorkerLeaseV1: ...
    def hold_unretained_worker(self, identity: ProcessV1, reason: str) -> Never: ...


@dataclass(frozen=True)
class RecordingOnlyResultV1:
    machine_id: str
    session_id: str
    worker: ProcessV1
    exit_code: int
    metadata_error: str | None
    normal_media: bool
    closure: Obj | None


def _body(resources: ResourcesV1, reference: RefV1) -> Obj:
    raw = resources.exact(reference)
    need(len(raw) == reference.bytes and hashlib.sha256(raw).hexdigest() == reference.sha256,
         "exact evidence bytes")
    value: object = json.loads(raw)
    return obj(value)


def run_recording_only_owner_v1(
    admission: RecordingOnlyAdmissionV1, *, capture: CaptureV1, publisher: PublisherV1,
    resources: ResourcesV1, now_utc: Callable[[], datetime],
) -> RecordingOnlyResultV1:
    a = parse_recording_only_admission_v1(admission.wire())
    need(resources.machine_id == a.machine_id, "actual execution machine")
    need(Path(__file__) == Path(a.evidence["controller"].path), "actual controller source")
    need(now_utc().astimezone(timezone.utc) < a.review_at, "finite admission expired")
    need(Path(capture.__file__) == Path(a.evidence["capture"].path)
         and Path(publisher.__file__) == Path(a.evidence["publisher_api"].path)
         and capture.decision_publisher_api() is publisher, "actual same capture/publisher modules")
    for reference in a.evidence.values():
        raw = resources.exact(reference)
        need(len(raw) == reference.bytes and hashlib.sha256(raw).hexdigest() == reference.sha256,
             "all exact source/input pins")
    need(all(resources.absent(p) for p in
             (a.requested.archive, a.current.archive, *a.outputs.values())), "create-only attempt")
    old_request = _body(resources, a.requested.before)
    need(old_request == _body(resources, a.current.before)
         and old_request.get("session_id") == a.old_session_id, "exact old canonical pair")
    job = _body(resources, a.evidence["old_job"])
    need(job.get("session_id") == a.old_session_id
         and job.get("pid") == a.game.pid
         and type(job.get("pid")) is int
         and type(job.get("game_creation_filetime")) is int
         and str(job["game_creation_filetime"]) == a.game.birth, "old job/Game")
    closed = _body(resources, a.evidence["old_obs_closed"])
    need(closed.get("machine_id") == a.machine_id and closed.get("pid") == a.old_obs.pid
         and type(closed.get("pid")) is int and closed.get("creation_filetime") == a.old_obs.birth
         and closed.get("process_exit_observed") is True
         and type(closed.get("wait_result")) is int and closed["wait_result"] == 0
         and type(closed.get("exit_code")) is int and closed["exit_code"] == 0
         and closed.get("normal_zero_exit") is True
         and closed.get("StopRecord_calls") == 0 and type(closed.get("StopRecord_calls")) is int,
         "actual independent normal old OBS close")
    obs_launch = _body(resources, a.evidence["old_obs_launch"])
    need(type(obs_launch.get("pid")) is int and obs_launch["pid"] == a.old_obs.pid
         and type(obs_launch.get("creation_filetime")) is int
         and str(obs_launch["creation_filetime"]) == a.old_obs.birth
         and Path(text(obs_launch.get("executable"))) == Path(a.old_obs.image)
         and closed.get("original_launch_ref") == a.evidence["old_obs_launch"].wire()
         and closed.get("original_worker_failed_ref") == a.evidence["old_failed"].wire(),
         "old OBS launch and failed capture provenance")
    need(type(old_request.get("worker_pid")) is int and old_request["worker_pid"] == a.old_worker.pid
         and type(old_request.get("worker_creation_filetime")) is int
         and str(old_request["worker_creation_filetime"]) == a.old_worker.birth
         and Path(text(old_request.get("worker_executable"))) == Path(a.old_worker.image),
         "old worker exact canonical source")
    state = _body(resources, a.evidence["old_closed_state"])
    old_worker = obj(state.get("old_worker"))
    need(state.get("machine_id") == a.machine_id
         and state.get("status") == "SAME_GAME_AND_PUBLISHER_LIVE_OLD_WORKER_AND_OBS_CLOSED"
         and state.get("Game") == a.game.wire() and state.get("publisher") == a.publisher.wire()
         and state.get("old_OBS_closed") == a.evidence["old_obs_closed"].wire()
         and state.get("old_request") == a.requested.before.wire()
         and state.get("publisher_started") == a.evidence["publisher_started"].wire()
         and type(old_worker.get("pid")) is int and old_worker["pid"] == a.old_worker.pid
         and old_worker.get("creation_filetime") == a.old_worker.birth
         and old_worker.get("kernel_exit_observed") is True
         and type(old_worker.get("wait_result")) is int and old_worker["wait_result"] == 0
         and type(old_worker.get("exit_code")) is int,
         "actual closed worker/OBS source; exited processes need not remain reopenable")
    resources.require_live(a.game)
    resources.require_live(a.publisher)
    launch = _body(resources, a.evidence["launch"])
    placement = _body(resources, a.evidence["placement"])
    need(type(launch.get("pid")) is int and launch["pid"] == a.game.pid
         and type(launch.get("creation_filetime")) is int
         and str(launch["creation_filetime"]) == a.game.birth
         and type(placement.get("pid")) is int and placement["pid"] == a.game.pid
         and type(placement.get("creation_filetime")) is int
         and str(placement["creation_filetime"]) == a.game.birth
         and placement.get("status") == "GREEN", "same actual launch/placement")
    hwnd = integer(placement.get("hwnd"), 1, 0xffffffffffffffff)
    publisher.read_text_binding(a.evidence["publisher_started"].wire(), game={
        "pid": a.game.pid, "creation_filetime": int(a.game.birth), "hwnd": hwnd,
        "desktop_id": text(placement.get("target_desktop_id"))})
    profile = _body(resources, a.evidence["profile"])
    capture.validate_profile(profile)
    old_profile = _body(resources, a.evidence["old_profile"])
    need(job.get("profile_path") == a.evidence["old_profile"].path
         and job.get("profile_sha256") == a.evidence["old_profile"].sha256, "old profile source")
    need(profile.get("continuous") is True
         and Path(text(profile.get("recording_root"))) == a.recording_root
         and type(profile.get("profile_name")) is str
         and profile.get("profile_name") != old_profile.get("profile_name")
         and profile.get("collection_name") != old_profile.get("collection_name")
         and "deadline_utc" in profile and profile["deadline_utc"] is None
         and "max_output_bytes" in profile and profile["max_output_bytes"] is None
         and stamp(profile.get("storage_review_at_utc")) >= a.review_at,
         "original continuous null contract and finite storage review")
    resources.write_new(a.outputs["intent"], {
        "schema": SCHEMA, "machine_id": a.machine_id, "admission_id": a.admission_id,
        "observed_at_utc": now_utc().isoformat(), "status": "ONCE_LAUNCH_INTENT",
        "old_session_id": a.old_session_id, "capture_source": a.evidence["capture"].wire(),
        "Game_stop_calls": 0, "publisher_stop_calls": 0, "replay_allowed": False})
    request = parse_worker_request_v1(capture.launch_recording(
        Path(a.evidence["profile"].path), a.recording_root, a.game.pid, hwnd, None,
        launch_receipt=Path(a.evidence["launch"].path), ffprobe=a.ffprobe,
        placement_receipt=Path(a.evidence["placement"].path),
        decision_publisher_receipt=Path(a.evidence["publisher_started"].path),
        continuous=True), a)
    try:
        worker = resources.retain_worker(request.worker)
    except Exception as error:
        resources.hold_unretained_worker(request.worker, str(error)[:1024])
    error_text: str | None = None
    closure: Obj | None = None
    normal = False
    try:
        try:
            _body(resources, a.requested.before)
            _body(resources, a.current.before)
            first, fid1, fid2 = resources.rename_exact(a.requested.before, a.requested.archive)
            second, fid3, fid4 = resources.rename_exact(a.current.before, a.current.archive)
            need((first.bytes, first.sha256) == (a.requested.before.bytes, a.requested.before.sha256)
                 and (second.bytes, second.sha256) == (a.current.before.bytes, a.current.before.sha256),
                 "archive preserves exact original bytes")
            resources.write_new(a.outputs["archived"], {
                "schema": "xar.recording-only-canonical-archive/v1", "machine_id": a.machine_id,
                "admission_id": a.admission_id, "observed_at_utc": now_utc().isoformat(),
                "requested_before": a.requested.before.wire(), "requested_archive": first.wire(),
                "current_before": a.current.before.wire(), "current_archive": second.wire(),
                "requested_source_file_id": fid1, "requested_archive_file_id": fid2,
                "current_source_file_id": fid3, "current_archive_file_id": fid4,
                "old_recording_directory_unchanged": True, "old_publisher_unchanged": True})
            wire = dict(request.legacy_request)
            wire.update(generation=a.generation, capture_admission_stage="saved_map",
                        map_ready_claimed=False)
            resources.write_new(a.requested.before.path, wire)
            resources.write_new(a.current.before.path, wire)
            resources.write_new(a.outputs["started"], {
                "schema": "xar.recording-only-owner-started/v1", "machine_id": a.machine_id,
                "admission_id": a.admission_id, "observed_at_utc": now_utc().isoformat(),
                "session_id": request.session_id, "worker": request.worker.wire(),
                "publisher_started": a.evidence["publisher_started"].wire(),
                "status": "NEW_WORKER_HANDLE_RETAINED_NOT_PIXEL_ADMITTED",
                "pixel_admitted": False, "old_session_id": a.old_session_id,
                "Game_stop_calls": 0, "publisher_stop_calls": 0, "replay_allowed": False})
        except Exception as error:
            error_text = str(error)[:1024]
        code = integer(worker.wait_exit(), 0)
        if code == 0 and error_text is None:
            try:
                closure = obj(capture.read_capture_closed_receipt(
                    request.root, session_id=request.session_id, game_pid=a.game.pid,
                    game_creation_filetime=int(a.game.birth),
                    recording_worker_pid=request.worker.pid, recording_root=a.recording_root))
                normal = True
            except Exception as error:
                error_text = str(error)[:1024]
        result = RecordingOnlyResultV1(a.machine_id, request.session_id, request.worker,
                                      code, error_text, normal, closure)
        resources.write_new(a.outputs["closed"], {
            "schema": "xar.recording-only-owner-closed/v1", "machine_id": a.machine_id,
            "admission_id": a.admission_id, "observed_at_utc": now_utc().isoformat(),
            "session_id": result.session_id, "worker": result.worker.wire(),
            "kernel_exit_observed": True, "worker_exit_code": code,
            "normal_capture_closure": normal, "capture_closed_proof": closure,
            "metadata_error": error_text, "Game_stop_calls": 0, "publisher_stop_calls": 0,
            "media_body_reads": 0, "pixel_admission_inferred": False, "replay_allowed": False})
        return result
    finally:
        worker.close()


@runtime_checkable
class NativeGenerationV1(Protocol):
    @property
    def handle(self) -> int: ...
    def check(self) -> None: ...
    def close(self) -> None: ...


@runtime_checkable
class GenerationFactoryV1(Protocol):
    def __call__(self, pid: int, executable: Path, *,
                 creation_filetime: int) -> NativeGenerationV1: ...


class NativeWorkerLeaseV1:
    def __init__(self, generation: NativeGenerationV1, kernel: object) -> None:
        self.generation = generation
        self.handle = integer(generation.handle, 1, 0xffffffffffffffff)
        self.kernel = kernel

    def wait_exit(self) -> int:
        import ctypes
        wait = getattr(self.kernel, "WaitForSingleObject")
        exit_code = getattr(self.kernel, "GetExitCodeProcess")
        while True:
            state = integer(wait(self.handle, 1000), 0)
            need(state in (0, 258), "retained worker kernel wait failed")
            if state == 0:
                value = ctypes.c_uint32()
                need(bool(exit_code(self.handle, ctypes.byref(value))), "worker exit query failed")
                return integer(value.value)
    def close(self) -> None:
        self.generation.close()


class LocalResourcesV1:
    """Concrete Windows adapter. No Game/publisher/OBS stop or force API exists."""
    def __init__(self, *, machine_id: str, attempt_root: Path, runtime_root: Path,
                 capture: CaptureV1) -> None:
        import ctypes
        from ctypes import wintypes
        self.machine_id = text(machine_id)
        self.root = attempt_root.resolve(strict=True)
        need(self.root.is_dir() and not self.root.is_symlink(), "actual independent attempt root")
        self.capture = capture
        self.runtime_root = runtime_root.resolve(strict=True)
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        k = self.kernel
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.OpenProcess.restype = wintypes.HANDLE
        k.GetProcessId.argtypes = [wintypes.HANDLE]
        k.GetProcessId.restype = wintypes.DWORD
        k.GetProcessTimes.argtypes = [wintypes.HANDLE, *[ctypes.POINTER(wintypes.FILETIME)] * 4]
        k.GetProcessTimes.restype = wintypes.BOOL
        k.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        k.WaitForSingleObject.restype = wintypes.DWORD
        k.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        k.GetExitCodeProcess.restype = wintypes.BOOL
        k.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                               wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        k.QueryFullProcessImageNameW.restype = wintypes.BOOL
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        k.CloseHandle.restype = wintypes.BOOL

    def exact(self, reference: RefV1) -> bytes:
        path = Path(reference.path)
        need(not path.is_symlink(), "source symlink rejected")
        before = path.stat()
        need(before.st_size == reference.bytes <= 1048576, "bounded source")
        with path.open("rb") as stream:
            body = stream.read(reference.bytes + 1)
        after = path.stat()
        need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
             == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
             and len(body) == reference.bytes
             and hashlib.sha256(body).hexdigest() == reference.sha256, "stable exact source")
        return body

    def absent(self, path: str) -> bool:
        p = Path(path)
        return not p.exists() and not p.is_symlink()

    def write_new(self, path: str, value: Obj) -> None:
        import os
        p = Path(path)
        need(p.parent == self.root or p in (
            self.runtime_root / "ROOT-OBS-RECORDING-REQUESTED-C23.json",
            self.runtime_root / "ROOT-CURRENT-OBS-RECORDING-REQUESTED-C23.json"), "declared output role")
        data = (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n").encode("utf-8")
        need(len(data) <= 32768, "bounded owner metadata")
        with p.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        need(p.read_bytes() == data, "metadata readback")

    def rename_exact(self, before: RefV1, archive: str) -> tuple[RefV1, str, str]:
        import os
        target = Path(archive)
        need(target.parent == self.root and self.absent(archive), "independent absent archive")
        self.exact(before)
        need(os.name == "nt", "production rotation requires Windows no-replace rename")
        origin = Path(before.path)
        source_id = origin.stat()
        origin.rename(target)
        target_id = target.stat()
        need((source_id.st_dev, source_id.st_ino) == (target_id.st_dev, target_id.st_ino)
             and not origin.exists(), "rename must preserve native file identity")
        result = RefV1(str(target), before.bytes, before.sha256)
        self.exact(result)
        return result, str(source_id.st_ino), str(target_id.st_ino)

    def _observe(self, identity: ProcessV1) -> tuple[int, int | None]:
        import ctypes
        from ctypes import wintypes
        k = self.kernel
        handle = k.OpenProcess(0x100000 | 0x1000, False, identity.pid)
        need(bool(handle), "exact process HANDLE unavailable")
        try:
            need(k.GetProcessId(handle) == identity.pid, "exact process PID")
            born, ended, kt, ut = (wintypes.FILETIME() for _ in range(4))
            need(bool(k.GetProcessTimes(handle, ctypes.byref(born), ctypes.byref(ended),
                                      ctypes.byref(kt), ctypes.byref(ut))), "process birth query")
            need(str((born.dwHighDateTime << 32) | born.dwLowDateTime) == identity.birth,
                 "exact process birth")
            state = integer(k.WaitForSingleObject(handle, 0))
            need(state in (0, 258), "process kernel state unknown")
            if state == 0:
                code = wintypes.DWORD()
                need(bool(k.GetExitCodeProcess(handle, ctypes.byref(code))), "process exit query")
                return state, integer(code.value)
            size = wintypes.DWORD(32768)
            image = ctypes.create_unicode_buffer(size.value)
            need(bool(k.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(size)))
                 and Path(image.value) == Path(identity.image), "actual live process image")
            return state, None
        finally:
            k.CloseHandle(handle)

    def require_live(self, identity: ProcessV1) -> None:
        need(self._observe(identity)[0] == 258, "borrowed exact process must be alive")

    def retain_worker(self, identity: ProcessV1) -> WorkerLeaseV1:
        helpers = self.capture._generation_helpers()
        need(isinstance(helpers, tuple) and bool(helpers), "actual generation helper tuple")
        if not isinstance(helpers, tuple) or not helpers:
            raise ValueError("generation helper tuple")
        factory = helpers[0]
        need(isinstance(factory, GenerationFactoryV1), "actual generation factory")
        if not isinstance(factory, GenerationFactoryV1):
            raise ValueError("generation factory")
        generation = factory(identity.pid, Path(identity.image), creation_filetime=int(identity.birth))
        need(isinstance(generation, NativeGenerationV1), "actual retained generation")
        generation.check()
        return NativeWorkerLeaseV1(generation, self.kernel)

    def hold_unretained_worker(self, identity: ProcessV1, reason: str) -> Never:
        import time
        while True:
            state, code = self._observe(identity)
            if state == 0:
                raise RuntimeError("worker custody unavailable; actual exit "
                                   + str(code) + "; no retry: " + reason)
            time.sleep(1)


def run_recording_only_from_file_v1(
    admission_ref: RefV1, *, expected_machine_id: str, capture: CaptureV1,
    publisher: PublisherV1,
) -> RecordingOnlyResultV1:
    """The Root runner loads existing N modules first, then this explicit file."""
    path = Path(admission_ref.path)
    need(path.stat().st_size == admission_ref.bytes <= 16384, "finite admission file")
    raw = path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == admission_ref.sha256, "admission source")
    value: object = json.loads(raw)
    admission = parse_recording_only_admission_v1(value)
    need(admission.machine_id == expected_machine_id, "actual execution machine")
    resources = LocalResourcesV1(machine_id=expected_machine_id,
                                attempt_root=admission.attempt_root,
                                runtime_root=admission.runtime_root, capture=capture)
    return run_recording_only_owner_v1(admission, capture=capture, publisher=publisher,
        resources=resources, now_utc=lambda: datetime.now(timezone.utc))
