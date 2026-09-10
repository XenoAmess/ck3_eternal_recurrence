"""Portable MCP handoff for jobs that must inherit an operator desktop.

The server is intentionally generic: operator identity, endpoint, commands,
paths, and process gates all come from a target-side JSON profile.  Starting
the server from the intended interactive desktop is a one-time deployment
boundary; jobs launched through it inherit that token and desktop.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import threading
import time
from typing import Callable, Mapping, Protocol, Sequence
import uuid


PROFILE_SCHEMA_VERSION = 1
SERVER_VERSION = "1.1.0"
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_PROCESS_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class OperatorProfileError(ValueError):
    """The target-side operator profile is malformed."""


class OperatorHandoffError(RuntimeError):
    """A controlled operator job cannot be handed off."""


@dataclass(frozen=True)
class RequiredPath:
    path: Path
    kind: str
    size: int | None = None
    sha256: str | None = None


@dataclass(frozen=True)
class OperatorJobProfile:
    name: str
    command: tuple[str, ...]
    working_directory: Path
    exclusive_process_names: tuple[str, ...]
    required_paths: tuple[RequiredPath, ...]
    absent_paths: tuple[Path, ...]
    controls: Mapping[str, bytes]


@dataclass(frozen=True)
class OperatorProfile:
    source_path: Path
    source_sha256: str
    target_id: str
    display_name: str
    expected_token_user: str
    expected_desktop: str
    expected_machine: str
    endpoint_transport: str
    endpoint_host: str
    endpoint_port: int
    advertised_url: str | None
    state_directory: Path
    jobs: Mapping[str, OperatorJobProfile]


@dataclass(frozen=True)
class HostIdentity:
    token_user: str
    desktop: str
    machine: str
    process_id: int


class ProcessInspector(Protocol):
    def pids(self, process_name: str) -> list[int]: ...


class ChildProcess(Protocol):
    pid: int
    stdin: object | None

    def poll(self) -> int | None: ...


@dataclass
class _JobRecord:
    job_id: str
    request_id: str
    job_name: str
    process: ChildProcess
    started_unix: float
    stdout_path: Path
    stderr_path: Path


@dataclass(frozen=True)
class _ControlRecord:
    target_id: str
    job_name: str
    job_id: str
    control_name: str
    response: Mapping[str, object]


def _require_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise OperatorProfileError(f"{label} must be an object")
    return value


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OperatorProfileError(f"{label} must be a non-empty string")
    return value


def _require_identifier(value: object, label: str) -> str:
    result = _require_string(value, label)
    if not _IDENTIFIER.fullmatch(result):
        raise OperatorProfileError(f"{label} is not a portable identifier")
    return result


def _absolute_path(value: object, label: str) -> Path:
    result = Path(_require_string(value, label))
    if not result.is_absolute():
        raise OperatorProfileError(f"{label} must be absolute")
    return result


def _string_list(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise OperatorProfileError(f"{label} must be a string array")
    return tuple(value)


def _load_controls(value: object, label: str) -> Mapping[str, bytes]:
    if value is None:
        return {}
    rows = _require_mapping(value, label)
    controls: dict[str, bytes] = {}
    for raw_name, raw_payload in rows.items():
        name = _require_identifier(raw_name, f"{label} key")
        if not isinstance(raw_payload, str):
            raise OperatorProfileError(f"{label}.{name} must be a string")
        controls[name] = raw_payload.encode("utf-8")
    return controls


def _load_required_path(value: object, label: str) -> RequiredPath:
    row = _require_mapping(value, label)
    kind = row.get("kind", "file")
    if kind not in {"file", "directory"}:
        raise OperatorProfileError(f"{label}.kind must be file or directory")
    size = row.get("size")
    if size is not None and (
        isinstance(size, bool) or not isinstance(size, int) or size < 0
    ):
        raise OperatorProfileError(f"{label}.size must be a non-negative integer")
    digest = row.get("sha256")
    if digest is not None:
        if not isinstance(digest, str) or not re.fullmatch(
            r"[0-9A-Fa-f]{64}", digest
        ):
            raise OperatorProfileError(f"{label}.sha256 must be 64 hex characters")
        digest = digest.upper()
    if kind == "directory" and (size is not None or digest is not None):
        raise OperatorProfileError(
            f"{label} cannot hash or size-check a directory"
        )
    return RequiredPath(
        path=_absolute_path(row.get("path"), f"{label}.path"),
        kind=kind,
        size=size,
        sha256=digest,
    )


def load_operator_profile(path: str | os.PathLike[str]) -> OperatorProfile:
    """Load and validate one target-side operator profile."""
    source_path = Path(path).resolve()
    source_bytes = source_path.read_bytes()
    try:
        payload = json.loads(source_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OperatorProfileError(f"operator profile is not UTF-8 JSON: {error}") from error
    root = _require_mapping(payload, "profile")
    if root.get("schema_version") != PROFILE_SCHEMA_VERSION:
        raise OperatorProfileError(
            f"schema_version must be {PROFILE_SCHEMA_VERSION}"
        )
    target = _require_mapping(root.get("target"), "target")
    expected = _require_mapping(target.get("expected"), "target.expected")
    endpoint = _require_mapping(root.get("endpoint"), "endpoint")
    transport = endpoint.get("transport", "streamable-http")
    if transport not in {"stdio", "streamable-http"}:
        raise OperatorProfileError(
            "endpoint.transport must be stdio or streamable-http"
        )
    host = _require_string(endpoint.get("host", "127.0.0.1"), "endpoint.host")
    port = endpoint.get("port", 8766)
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise OperatorProfileError("endpoint.port must be an integer from 1 to 65535")
    advertised_url = endpoint.get("advertised_url")
    if advertised_url is not None:
        advertised_url = _require_string(
            advertised_url, "endpoint.advertised_url"
        )

    jobs_payload = _require_mapping(root.get("jobs"), "jobs")
    if not jobs_payload:
        raise OperatorProfileError("jobs must contain at least one configured job")
    jobs: dict[str, OperatorJobProfile] = {}
    for raw_name, raw_job in jobs_payload.items():
        name = _require_identifier(raw_name, "jobs key")
        job = _require_mapping(raw_job, f"jobs.{name}")
        command = _string_list(job.get("command"), f"jobs.{name}.command")
        if not command:
            raise OperatorProfileError(f"jobs.{name}.command cannot be empty")
        executable = Path(command[0])
        if not executable.is_absolute():
            raise OperatorProfileError(
                f"jobs.{name}.command[0] must be an absolute executable path"
            )
        process_names = _string_list(
            job.get("exclusive_process_names", []),
            f"jobs.{name}.exclusive_process_names",
        )
        if any(not _PROCESS_NAME.fullmatch(item) for item in process_names):
            raise OperatorProfileError(
                f"jobs.{name}.exclusive_process_names contains an invalid name"
            )
        required_payload = job.get("required_paths", [])
        if not isinstance(required_payload, list):
            raise OperatorProfileError(
                f"jobs.{name}.required_paths must be an array"
            )
        required_paths = tuple(
            _load_required_path(item, f"jobs.{name}.required_paths[{index}]")
            for index, item in enumerate(required_payload)
        )
        absent_payload = job.get("absent_paths", [])
        if not isinstance(absent_payload, list):
            raise OperatorProfileError(f"jobs.{name}.absent_paths must be an array")
        absent_paths = tuple(
            _absolute_path(item, f"jobs.{name}.absent_paths[{index}]")
            for index, item in enumerate(absent_payload)
        )
        jobs[name] = OperatorJobProfile(
            name=name,
            command=command,
            working_directory=_absolute_path(
                job.get("working_directory"),
                f"jobs.{name}.working_directory",
            ),
            exclusive_process_names=process_names,
            required_paths=required_paths,
            absent_paths=absent_paths,
            controls=_load_controls(job.get("controls"), f"jobs.{name}.controls"),
        )

    return OperatorProfile(
        source_path=source_path,
        source_sha256=hashlib.sha256(source_bytes).hexdigest().upper(),
        target_id=_require_identifier(target.get("id"), "target.id"),
        display_name=_require_string(target.get("display_name"), "target.display_name"),
        expected_token_user=_require_string(
            expected.get("token_user"), "target.expected.token_user"
        ),
        expected_desktop=_require_string(
            expected.get("desktop"), "target.expected.desktop"
        ),
        expected_machine=_require_string(
            expected.get("machine"), "target.expected.machine"
        ),
        endpoint_transport=transport,
        endpoint_host=host,
        endpoint_port=port,
        advertised_url=advertised_url,
        state_directory=_absolute_path(root.get("state_directory"), "state_directory"),
        jobs=jobs,
    )


def _windows_token_user() -> str:
    size = wintypes.DWORD(0)
    ctypes.windll.advapi32.GetUserNameW(None, ctypes.byref(size))
    buffer = ctypes.create_unicode_buffer(size.value)
    if not ctypes.windll.advapi32.GetUserNameW(buffer, ctypes.byref(size)):
        raise ctypes.WinError()
    return buffer.value


def _windows_object_name(handle: int) -> str:
    size = wintypes.DWORD(0)
    ctypes.windll.user32.GetUserObjectInformationW(
        handle, 2, None, 0, ctypes.byref(size)
    )
    buffer = ctypes.create_unicode_buffer(max(1, size.value // 2))
    if not ctypes.windll.user32.GetUserObjectInformationW(
        handle,
        2,
        buffer,
        ctypes.sizeof(buffer),
        ctypes.byref(size),
    ):
        raise ctypes.WinError()
    return buffer.value


def current_host_identity() -> HostIdentity:
    """Return the real process token and desktop, not inherited env labels."""
    if os.name == "nt":
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        window_station = user32.GetProcessWindowStation()
        thread_desktop = user32.GetThreadDesktop(kernel32.GetCurrentThreadId())
        token_user = _windows_token_user()
        desktop = (
            f"{_windows_object_name(window_station)}\\"
            f"{_windows_object_name(thread_desktop)}"
        )
    else:
        import getpass

        token_user = getpass.getuser()
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "unavailable")
    return HostIdentity(
        token_user=token_user,
        desktop=desktop,
        machine=platform.node(),
        process_id=os.getpid(),
    )


class NativeProcessInspector:
    """Enumerate exact process-image names without an account-specific helper."""

    def pids(self, process_name: str) -> list[int]:
        if not _PROCESS_NAME.fullmatch(process_name):
            raise ValueError("invalid process name")
        if os.name == "nt":
            stem = process_name[:-4] if process_name.lower().endswith(".exe") else process_name
            script = (
                "$items=@(Get-Process -Name '"
                + stem
                + "' -ErrorAction SilentlyContinue); "
                "@($items | ForEach-Object {[int]$_.Id}) | ConvertTo-Json -Compress"
            )
            completed = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    script,
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            raw = completed.stdout.strip()
            if not raw:
                return []
            value = json.loads(raw)
            rows = value if isinstance(value, list) else [value]
            return sorted(int(item) for item in rows)
        result: list[int] = []
        for child in Path("/proc").iterdir():
            if not child.name.isdigit():
                continue
            try:
                observed = (child / "comm").read_text(encoding="utf-8").strip()
            except OSError:
                continue
            if observed == process_name:
                result.append(int(child.name))
        return sorted(result)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _job_spec_sha256(job: OperatorJobProfile) -> str:
    payload = {
        "name": job.name,
        "command": list(job.command),
        "working_directory": str(job.working_directory),
        "exclusive_process_names": list(job.exclusive_process_names),
        "required_paths": [
            {
                "path": str(item.path),
                "kind": item.kind,
                "size": item.size,
                "sha256": item.sha256,
            }
            for item in job.required_paths
        ],
        "absent_paths": [str(item) for item in job.absent_paths],
        "controls": {
            name: hashlib.sha256(payload).hexdigest().upper()
            for name, payload in sorted(job.controls.items())
        },
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


class OperatorService:
    """Read target state and hand off only commands frozen in the profile."""

    def __init__(
        self,
        profile: OperatorProfile,
        *,
        identity_probe: Callable[[], HostIdentity] = current_host_identity,
        process_inspector: ProcessInspector | None = None,
        popen_factory: Callable[..., ChildProcess] = subprocess.Popen,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.profile = profile
        self._identity_probe = identity_probe
        self._process_inspector = process_inspector or NativeProcessInspector()
        self._popen_factory = popen_factory
        self._clock = clock
        self._server_instance_id = str(uuid.uuid4())
        # handoff holds this lock across its final preflight and spawn; the
        # preflight also reads the job table, so re-entry is intentional.
        self._lock = threading.RLock()
        self._jobs: dict[str, _JobRecord] = {}
        self._requests: dict[str, str] = {}
        self._control_requests: dict[str, _ControlRecord] = {}

    def _identity(self) -> HostIdentity:
        return self._identity_probe()

    def _identity_payload(self, identity: HostIdentity) -> dict[str, object]:
        return {
            "token_user": identity.token_user,
            "desktop": identity.desktop,
            "machine": identity.machine,
            "process_id": identity.process_id,
        }

    def _assert_target(self, target_id: str) -> None:
        if target_id != self.profile.target_id:
            raise OperatorHandoffError(
                f"target mismatch: {target_id!r} != {self.profile.target_id!r}"
            )

    def _job(self, job_name: str) -> OperatorJobProfile:
        try:
            return self.profile.jobs[job_name]
        except KeyError as error:
            raise OperatorHandoffError(
                f"job is not configured for target {self.profile.target_id}: {job_name}"
            ) from error

    def capabilities(self) -> dict[str, object]:
        endpoint = {
            "transport": self.profile.endpoint_transport,
            "host": self.profile.endpoint_host,
            "port": self.profile.endpoint_port,
        }
        if self.profile.advertised_url is not None:
            endpoint["advertised_url"] = self.profile.advertised_url
        return {
            "schema_version": 1,
            "server_version": SERVER_VERSION,
            "server_instance_id": self._server_instance_id,
            "target_id": self.profile.target_id,
            "display_name": self.profile.display_name,
            "profile_sha256": self.profile.source_sha256,
            "endpoint": endpoint,
            "jobs": sorted(self.profile.jobs),
            "job_controls": {
                name: sorted(job.controls)
                for name, job in sorted(self.profile.jobs.items())
            },
            "tools": [
                "operator_get_capabilities",
                "operator_get_status",
                "operator_preflight_job",
                "operator_handoff_job",
                "operator_control_job",
            ],
            "caller_supplied_commands": False,
            "operator_bootstrap_required": True,
        }

    def _record_payload(self, record: _JobRecord) -> dict[str, object]:
        exit_code = record.process.poll()
        job = self.profile.jobs[record.job_name]
        return {
            "job_id": record.job_id,
            "request_id": record.request_id,
            "job_name": record.job_name,
            "pid": record.process.pid,
            "state": "running" if exit_code is None else "exited",
            "exit_code": exit_code,
            "started_unix": record.started_unix,
            "stdout_path": str(record.stdout_path),
            "stderr_path": str(record.stderr_path),
            "available_controls": sorted(job.controls),
        }

    def status(self, target_id: str) -> dict[str, object]:
        self._assert_target(target_id)
        identity = self._identity()
        process_gates: dict[str, list[int]] = {}
        names = sorted(
            {
                name
                for job in self.profile.jobs.values()
                for name in job.exclusive_process_names
            }
        )
        errors: dict[str, str] = {}
        for name in names:
            try:
                process_gates[name] = self._process_inspector.pids(name)
            except Exception as error:  # status must preserve an unreadable gate
                errors[name] = f"{type(error).__name__}: {error}"
        with self._lock:
            jobs = [self._record_payload(item) for item in self._jobs.values()]
        return {
            "schema_version": 1,
            "server_instance_id": self._server_instance_id,
            "target_id": self.profile.target_id,
            "identity": self._identity_payload(identity),
            "identity_matches_profile": self._identity_matches(identity),
            "process_gates": process_gates,
            "process_gate_errors": errors,
            "jobs": jobs,
        }

    def _identity_matches(self, identity: HostIdentity) -> bool:
        return (
            identity.token_user.casefold()
            == self.profile.expected_token_user.casefold()
            and identity.desktop.casefold()
            == self.profile.expected_desktop.casefold()
            and identity.machine.casefold()
            == self.profile.expected_machine.casefold()
        )

    def preflight_job(self, target_id: str, job_name: str) -> dict[str, object]:
        self._assert_target(target_id)
        job = self._job(job_name)
        identity = self._identity()
        checks: dict[str, bool] = {
            "target_identity_exact": self._identity_matches(identity),
            "working_directory_present": job.working_directory.is_dir(),
            "executable_present": Path(job.command[0]).is_file(),
        }
        observations: dict[str, object] = {
            "identity": self._identity_payload(identity),
            "process_gates": {},
            "required_paths": [],
            "absent_paths": [],
        }
        process_gate_errors: dict[str, str] = {}
        for name in job.exclusive_process_names:
            try:
                pids = self._process_inspector.pids(name)
            except Exception as error:
                pids = []
                process_gate_errors[name] = f"{type(error).__name__}: {error}"
            observations["process_gates"][name] = pids
            checks[f"process_absent:{name}"] = not pids and name not in process_gate_errors

        for index, required in enumerate(job.required_paths):
            exists = (
                required.path.is_file()
                if required.kind == "file"
                else required.path.is_dir()
            )
            row: dict[str, object] = {
                "path": str(required.path),
                "kind": required.kind,
                "exists": exists,
            }
            exact = exists
            if exists and required.kind == "file":
                observed_size = required.path.stat().st_size
                row["size"] = observed_size
                if required.size is not None:
                    exact = exact and observed_size == required.size
                if required.sha256 is not None:
                    observed_sha256 = _sha256(required.path)
                    row["sha256"] = observed_sha256
                    exact = exact and observed_sha256 == required.sha256
            checks[f"required_path:{index}"] = exact
            observations["required_paths"].append(row)

        for index, absent in enumerate(job.absent_paths):
            missing = not absent.exists()
            checks[f"path_absent:{index}"] = missing
            observations["absent_paths"].append(
                {"path": str(absent), "absent": missing}
            )

        with self._lock:
            running_jobs = [
                record.job_id
                for record in self._jobs.values()
                if record.process.poll() is None
            ]
        checks["no_active_operator_job"] = not running_jobs
        failed = sorted(name for name, passed in checks.items() if not passed)
        evidence = {
            "target_id": target_id,
            "job_name": job_name,
            "profile_sha256": self.profile.source_sha256,
            "job_spec_sha256": _job_spec_sha256(job),
            "checks": checks,
            "observations": observations,
            "process_gate_errors": process_gate_errors,
            "running_job_ids": running_jobs,
        }
        evidence_sha256 = hashlib.sha256(
            json.dumps(
                evidence,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest().upper()
        return {
            "schema_version": 1,
            "result": "GREEN" if not failed else "RED",
            **evidence,
            "failed_checks": failed,
            "evidence_sha256": evidence_sha256,
        }

    def handoff_job(
        self,
        target_id: str,
        job_name: str,
        request_id: str,
    ) -> dict[str, object]:
        """Start exactly one configured job after a same-call target preflight."""
        self._assert_target(target_id)
        if not isinstance(request_id, str) or not _IDENTIFIER.fullmatch(request_id):
            raise OperatorHandoffError("request_id must be a portable identifier")
        job = self._job(job_name)
        with self._lock:
            prior_id = self._requests.get(request_id)
            if prior_id is not None:
                prior = self._jobs[prior_id]
                if prior.job_name != job_name:
                    raise OperatorHandoffError(
                        "request_id is already bound to a different job"
                    )
                return {
                    "schema_version": 1,
                    "result": "ACCEPTED",
                    "idempotent_replay": True,
                    "target_id": target_id,
                    "profile_sha256": self.profile.source_sha256,
                    "job": self._record_payload(prior),
                }
            if any(record.process.poll() is None for record in self._jobs.values()):
                raise OperatorHandoffError("another operator job is already running")

            preflight = self.preflight_job(target_id, job_name)
            if preflight["result"] != "GREEN":
                raise OperatorHandoffError(
                    "operator preflight RED: "
                    + ", ".join(preflight["failed_checks"])
                )
            job_id = str(uuid.uuid4())
            job_directory = self.profile.state_directory / "jobs" / job_id
            job_directory.mkdir(parents=True, exist_ok=False)
            stdout_path = job_directory / "stdout.log"
            stderr_path = job_directory / "stderr.log"
            with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
                process = self._popen_factory(
                    list(job.command),
                    cwd=str(job.working_directory),
                    stdin=subprocess.PIPE if job.controls else subprocess.DEVNULL,
                    stdout=stdout,
                    stderr=stderr,
                    close_fds=True,
                )
            record = _JobRecord(
                job_id=job_id,
                request_id=request_id,
                job_name=job_name,
                process=process,
                started_unix=self._clock(),
                stdout_path=stdout_path,
                stderr_path=stderr_path,
            )
            self._jobs[job_id] = record
            self._requests[request_id] = job_id
            manifest = {
                "schema_version": 1,
                "server_instance_id": self._server_instance_id,
                "target_id": target_id,
                "profile_sha256": self.profile.source_sha256,
                "job_spec_sha256": _job_spec_sha256(job),
                "preflight_evidence_sha256": preflight["evidence_sha256"],
                "job": self._record_payload(record),
            }
            (job_directory / "handoff.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
            return {
                "schema_version": 1,
                "result": "ACCEPTED",
                "idempotent_replay": False,
                "target_id": target_id,
                "profile_sha256": self.profile.source_sha256,
                "preflight": preflight,
                "job": self._record_payload(record),
            }

    def control_job(
        self,
        target_id: str,
        job_name: str,
        job_id: str,
        control_name: str,
        request_id: str,
    ) -> dict[str, object]:
        """Send one profile-frozen stdin control to the matching live job."""
        self._assert_target(target_id)
        if not isinstance(job_id, str) or not _IDENTIFIER.fullmatch(job_id):
            raise OperatorHandoffError("job_id must be a portable identifier")
        if not isinstance(control_name, str) or not _IDENTIFIER.fullmatch(
            control_name
        ):
            raise OperatorHandoffError("control_name must be a portable identifier")
        if not isinstance(request_id, str) or not _IDENTIFIER.fullmatch(request_id):
            raise OperatorHandoffError("request_id must be a portable identifier")
        job = self._job(job_name)
        with self._lock:
            prior = self._control_requests.get(request_id)
            if prior is not None:
                if (
                    prior.target_id != target_id
                    or prior.job_name != job_name
                    or prior.job_id != job_id
                    or prior.control_name != control_name
                ):
                    raise OperatorHandoffError(
                        "request_id is already bound to a different job control"
                    )
                return {**prior.response, "idempotent_replay": True}

            try:
                record = self._jobs[job_id]
            except KeyError as error:
                raise OperatorHandoffError(
                    f"operator job does not exist: {job_id}"
                ) from error
            if record.job_name != job_name:
                raise OperatorHandoffError("job_id is bound to a different job")
            try:
                payload = job.controls[control_name]
            except KeyError as error:
                raise OperatorHandoffError(
                    f"control is not configured for job {job_name}: {control_name}"
                ) from error
            exit_code = record.process.poll()
            if exit_code is not None:
                raise OperatorHandoffError(
                    f"operator job already exited with code {exit_code}"
                )

            response: dict[str, object] = {
                "schema_version": 1,
                "result": "ACCEPTED",
                "idempotent_replay": False,
                "target_id": target_id,
                "profile_sha256": self.profile.source_sha256,
                "job_id": job_id,
                "job_name": job_name,
                "control_name": control_name,
                "payload_bytes": len(payload),
            }
            try:
                stream = record.process.stdin
                if stream is None:
                    raise BrokenPipeError("configured job has no stdin pipe")
                written = stream.write(payload)  # type: ignore[attr-defined]
                if written != len(payload):
                    raise OSError(
                        f"short stdin write: {written!r} of {len(payload)} bytes"
                    )
                stream.flush()  # type: ignore[attr-defined]
            except (OSError, ValueError) as error:
                response["result"] = "RED"
                response["error"] = f"{type(error).__name__}: {error}"
            control_record = _ControlRecord(
                target_id=target_id,
                job_name=job_name,
                job_id=job_id,
                control_name=control_name,
                response=response,
            )
            self._control_requests[request_id] = control_record
            return dict(response)


def create_operator_server(service: OperatorService):
    """Build the generic target-side MCP server lazily."""
    try:
        from mcp.server import MCPServer
        from mcp.types import ToolAnnotations
    except ImportError as error:
        raise RuntimeError(
            "operator MCP mode requires: pip install 'mcp==2.0.0'"
        ) from error

    server = MCPServer(
        name="Xar Portable Operator Handoff",
        version=SERVER_VERSION,
        instructions=(
            "Select the configured target_id, read capabilities/status, then run "
            "operator_preflight_job. Call operator_handoff_job only for a GREEN "
            "preflight. Job commands and stdin controls are target-profile data."
        ),
    )
    read_only = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )
    handoff = ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )

    @server.tool(annotations=read_only)
    def operator_get_capabilities() -> dict[str, object]:
        """Read this target's versioned operator/job capabilities."""
        return service.capabilities()

    @server.tool(annotations=read_only)
    def operator_get_status(target_id: str) -> dict[str, object]:
        """Read token, desktop, process gates, and handed-off job state."""
        return service.status(target_id)

    @server.tool(annotations=read_only)
    def operator_preflight_job(
        target_id: str, job_name: str
    ) -> dict[str, object]:
        """Read identity, input, output, and exclusive-process readiness."""
        return service.preflight_job(target_id, job_name)

    @server.tool(annotations=handoff)
    def operator_handoff_job(
        target_id: str, job_name: str, request_id: str
    ) -> dict[str, object]:
        """Start one profile-frozen job; request_id makes retries idempotent."""
        return service.handoff_job(target_id, job_name, request_id)

    @server.tool(annotations=handoff)
    def operator_control_job(
        target_id: str,
        job_name: str,
        job_id: str,
        control_name: str,
        request_id: str,
    ) -> dict[str, object]:
        """Send one profile-frozen control to the matching running job."""
        return service.control_job(
            target_id, job_name, job_id, control_name, request_id
        )

    @server.resource("operator://capabilities")
    def operator_capabilities_resource() -> dict[str, object]:
        return service.capabilities()

    return server


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="xar-operator-mcp")
    result.add_argument(
        "--profile",
        type=Path,
        required=True,
        help="target-side UTF-8 JSON operator profile",
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    profile = load_operator_profile(args.profile)
    profile.state_directory.mkdir(parents=True, exist_ok=True)
    service = OperatorService(profile)
    server = create_operator_server(service)
    if profile.endpoint_transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(
            transport="streamable-http",
            host=profile.endpoint_host,
            port=profile.endpoint_port,
            stateless_http=False,
            json_response=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
