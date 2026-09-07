"""Exact-build, read-only timing probe for CK3's particle2 slot zero.

The probe observes only three pointer-sized values in one authenticated CK3
process: ``module + 0x570F908``, ``manager + 0xA8``, and the graphics global at
``module + 0x570FC60``.  It never allocates or writes target memory and it is
disabled unless a caller explicitly prepares and starts a probe plan.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import ctypes
from ctypes import wintypes
import hashlib
import math
import os
from pathlib import Path
import threading
import time
from typing import Callable, Protocol

from .environment import write_json_atomic
from .errors import AgentError


EXPECTED_CK3_EXE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
STARTUP_SLOT0_ROOT_GLOBAL_RVA = 0x570F908
STARTUP_SLOT0_GRAPHICS_GLOBAL_RVA = 0x570FC60
STARTUP_SLOT0_MANAGER_OFFSET = 0xA8
STARTUP_SLOT0_POINTER_BYTES = 8
STARTUP_SLOT0_DEFAULT_POLL_INTERVAL_SECONDS = 0.005
STARTUP_SLOT0_DEFAULT_MAX_DURATION_SECONDS = 300.0
STARTUP_SLOT0_FINISH_GRACE_SECONDS = 2.0
STARTUP_SLOT0_MAX_RECORDED_ERRORS = 64
STARTUP_SLOT0_MODULE_DISCOVERY_RETRY_WINERRORS = frozenset({24, 299})
STARTUP_SLOT0_MODULE_DISCOVERY_TIMEOUT_SECONDS = 1.0
STARTUP_SLOT0_MODULE_DISCOVERY_POLL_SECONDS = 0.005


class _StartupSlot0Reader(Protocol):
    """Minimal read-only target interface, injectable for offline tests."""

    image_path: Path
    module_base: int

    def exit_code(self) -> int | None: ...

    def read_pointer(self, address: int) -> int: ...

    def close(self) -> None: ...


@dataclass(frozen=True)
class StartupSlot0ModuleDiscovery:
    module_base: int
    attempts: int
    transient_error_count: int
    elapsed_seconds: float


class StartupSlot0ModuleDiscoveryError(AgentError):
    """Bounded module discovery ended without an authenticated base."""

    def __init__(
        self,
        *,
        reason: str,
        attempts: int,
        transient_error_count: int,
        elapsed_seconds: float,
        last_error: BaseException | None = None,
        process_exit_code: int | None = None,
    ) -> None:
        self.reason = reason
        self.attempts = attempts
        self.transient_error_count = transient_error_count
        self.elapsed_seconds = round(max(0.0, elapsed_seconds), 6)
        self.process_exit_code = process_exit_code
        self.last_error = last_error
        winerror = getattr(last_error, "winerror", None)
        if not isinstance(winerror, int):
            winerror = getattr(last_error, "errno", None)
        self.winerror = winerror if isinstance(winerror, int) else None
        detail = (
            f"; last_error={type(last_error).__name__}: {last_error}"
            if last_error is not None
            else ""
        )
        exit_detail = (
            f"; process_exit_code={process_exit_code}"
            if process_exit_code is not None
            else ""
        )
        super().__init__(
            "startup slot0 module discovery failed: "
            f"reason={reason}; attempts={attempts}; "
            f"transient_errors={transient_error_count}; "
            f"elapsed_seconds={self.elapsed_seconds:.6f}"
            f"{exit_detail}{detail}"
        )

    def evidence(self) -> dict[str, object]:
        return {
            "status": self.reason,
            "attempts": self.attempts,
            "transient_error_count": self.transient_error_count,
            "elapsed_seconds": self.elapsed_seconds,
            "last_winerror": self.winerror,
            "last_error": (
                f"{type(self.last_error).__name__}: {self.last_error}"
                if self.last_error is not None
                else None
            ),
            "process_exit_code": self.process_exit_code,
        }


def _retry_module_discovery(
    query_once: Callable[[], int],
    process_exit_code: Callable[[], int | None],
    *,
    timeout_seconds: float = STARTUP_SLOT0_MODULE_DISCOVERY_TIMEOUT_SECONDS,
    poll_interval_seconds: float = STARTUP_SLOT0_MODULE_DISCOVERY_POLL_SECONDS,
    sleeper: Callable[[float], None] = time.sleep,
    monotonic: Callable[[], float] = time.monotonic,
) -> StartupSlot0ModuleDiscovery:
    """Retry only Toolhelp's documented short startup races, fail closed."""

    started = monotonic()
    attempts = 0
    transient_error_count = 0
    last_error: BaseException | None = None
    while True:
        elapsed = max(0.0, monotonic() - started)
        try:
            exit_code = process_exit_code()
        except BaseException as error:
            raise StartupSlot0ModuleDiscoveryError(
                reason="process_exit_probe_error",
                attempts=attempts,
                transient_error_count=transient_error_count,
                elapsed_seconds=elapsed,
                last_error=error,
            ) from error
        if exit_code is not None:
            raise StartupSlot0ModuleDiscoveryError(
                reason="process_exit",
                attempts=attempts,
                transient_error_count=transient_error_count,
                elapsed_seconds=elapsed,
                last_error=last_error,
                process_exit_code=exit_code,
            )
        if elapsed >= timeout_seconds:
            raise StartupSlot0ModuleDiscoveryError(
                reason="timeout",
                attempts=attempts,
                transient_error_count=transient_error_count,
                elapsed_seconds=elapsed,
                last_error=last_error,
            )
        attempts += 1
        try:
            module_base = query_once()
        except OSError as error:
            winerror = getattr(error, "winerror", None)
            if not isinstance(winerror, int):
                winerror = getattr(error, "errno", None)
            if winerror not in STARTUP_SLOT0_MODULE_DISCOVERY_RETRY_WINERRORS:
                raise StartupSlot0ModuleDiscoveryError(
                    reason="non_transient_error",
                    attempts=attempts,
                    transient_error_count=transient_error_count,
                    elapsed_seconds=max(0.0, monotonic() - started),
                    last_error=error,
                ) from error
            transient_error_count += 1
            last_error = error
        except BaseException as error:
            raise StartupSlot0ModuleDiscoveryError(
                reason="non_transient_error",
                attempts=attempts,
                transient_error_count=transient_error_count,
                elapsed_seconds=max(0.0, monotonic() - started),
                last_error=error,
            ) from error
        else:
            if (
                isinstance(module_base, bool)
                or not isinstance(module_base, int)
                or module_base <= 0
            ):
                error = AgentError(
                    "module discovery returned a non-positive module base"
                )
                raise StartupSlot0ModuleDiscoveryError(
                    reason="invalid_module_base",
                    attempts=attempts,
                    transient_error_count=transient_error_count,
                    elapsed_seconds=max(0.0, monotonic() - started),
                    last_error=error,
                ) from error
            return StartupSlot0ModuleDiscovery(
                module_base=module_base,
                attempts=attempts,
                transient_error_count=transient_error_count,
                elapsed_seconds=round(
                    max(0.0, monotonic() - started), 6
                ),
            )
        remaining = timeout_seconds - max(0.0, monotonic() - started)
        if remaining > 0:
            sleeper(min(poll_interval_seconds, remaining))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left.resolve())) == os.path.normcase(
        str(right.resolve())
    )


def _hex_pointer(value: int | None) -> str | None:
    return None if value is None else f"0x{value:016X}"


class _ModuleEntry32W(ctypes.Structure):
    _fields_ = (
        ("dwSize", wintypes.DWORD),
        ("th32ModuleID", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("GlblcntUsage", wintypes.DWORD),
        ("ProccntUsage", wintypes.DWORD),
        ("modBaseAddr", ctypes.POINTER(ctypes.c_byte)),
        ("modBaseSize", wintypes.DWORD),
        ("hModule", wintypes.HMODULE),
        ("szModule", wintypes.WCHAR * 256),
        ("szExePath", wintypes.WCHAR * 260),
    )


class WindowsStartupSlot0Reader:
    """Read-only Win32 process reader for one already-launched CK3 PID."""

    _PROCESS_VM_READ = 0x0010
    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    _SYNCHRONIZE = 0x00100000
    _TH32CS_SNAPMODULE = 0x00000008
    _TH32CS_SNAPMODULE32 = 0x00000010
    _INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
    _STILL_ACTIVE = 259

    def __init__(self, pid: int, expected_executable: Path) -> None:
        if os.name != "nt":
            raise AgentError("startup slot0 probe requires Windows")
        if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
            raise AgentError("startup slot0 probe PID must be positive")
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._handle: int | None = None
        self.image_path = Path()
        self.module_base = 0
        self.module_discovery_attempts = 0
        self.module_discovery_transient_error_count = 0
        self.module_discovery_elapsed_seconds = 0.0
        self._configure_functions()
        handle = self._open_process(
            self._PROCESS_VM_READ
            | self._PROCESS_QUERY_LIMITED_INFORMATION
            | self._SYNCHRONIZE,
            False,
            pid,
        )
        if not handle:
            self._raise_last_error("OpenProcess")
        self._handle = int(handle)
        try:
            self.image_path = self._query_image_path()
            if not _same_path(self.image_path, expected_executable):
                raise AgentError(
                    "startup slot0 probe process image differs from admitted "
                    f"executable: {self.image_path} != {expected_executable}"
                )
            discovery = _retry_module_discovery(
                lambda: self._query_module_base(pid, expected_executable),
                self.exit_code,
            )
            self.module_base = discovery.module_base
            self.module_discovery_attempts = discovery.attempts
            self.module_discovery_transient_error_count = (
                discovery.transient_error_count
            )
            self.module_discovery_elapsed_seconds = discovery.elapsed_seconds
            if self.module_base <= 0:
                raise AgentError("startup slot0 probe module base is not positive")
        except BaseException:
            self.close()
            raise

    def _configure_functions(self) -> None:
        self._open_process = self._kernel32.OpenProcess
        self._open_process.argtypes = (
            wintypes.DWORD,
            wintypes.BOOL,
            wintypes.DWORD,
        )
        self._open_process.restype = wintypes.HANDLE
        self._close_handle = self._kernel32.CloseHandle
        self._close_handle.argtypes = (wintypes.HANDLE,)
        self._close_handle.restype = wintypes.BOOL
        self._query_full_process_image_name = (
            self._kernel32.QueryFullProcessImageNameW
        )
        self._query_full_process_image_name.argtypes = (
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        )
        self._query_full_process_image_name.restype = wintypes.BOOL
        self._read_process_memory = self._kernel32.ReadProcessMemory
        self._read_process_memory.argtypes = (
            wintypes.HANDLE,
            wintypes.LPCVOID,
            wintypes.LPVOID,
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
        )
        self._read_process_memory.restype = wintypes.BOOL
        self._get_exit_code_process = self._kernel32.GetExitCodeProcess
        self._get_exit_code_process.argtypes = (
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.DWORD),
        )
        self._get_exit_code_process.restype = wintypes.BOOL
        self._create_toolhelp_snapshot = (
            self._kernel32.CreateToolhelp32Snapshot
        )
        self._create_toolhelp_snapshot.argtypes = (
            wintypes.DWORD,
            wintypes.DWORD,
        )
        self._create_toolhelp_snapshot.restype = wintypes.HANDLE
        self._module32_first = self._kernel32.Module32FirstW
        self._module32_first.argtypes = (
            wintypes.HANDLE,
            ctypes.POINTER(_ModuleEntry32W),
        )
        self._module32_first.restype = wintypes.BOOL
        self._module32_next = self._kernel32.Module32NextW
        self._module32_next.argtypes = (
            wintypes.HANDLE,
            ctypes.POINTER(_ModuleEntry32W),
        )
        self._module32_next.restype = wintypes.BOOL

    @staticmethod
    def _raise_last_error(operation: str) -> None:
        error = int(ctypes.get_last_error())
        raise OSError(error, f"{operation} failed: {ctypes.FormatError(error)}")

    def _query_image_path(self) -> Path:
        assert self._handle is not None
        capacity = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(capacity.value)
        if not self._query_full_process_image_name(
            self._handle, 0, buffer, ctypes.byref(capacity)
        ):
            self._raise_last_error("QueryFullProcessImageNameW")
        return Path(buffer.value).resolve()

    def _query_module_base(self, pid: int, expected_executable: Path) -> int:
        snapshot = self._create_toolhelp_snapshot(
            self._TH32CS_SNAPMODULE | self._TH32CS_SNAPMODULE32, pid
        )
        snapshot_value = int(snapshot) if snapshot else 0
        if not snapshot or snapshot_value == self._INVALID_HANDLE_VALUE:
            self._raise_last_error("CreateToolhelp32Snapshot(module)")
        try:
            entry = _ModuleEntry32W()
            entry.dwSize = ctypes.sizeof(_ModuleEntry32W)
            present = bool(self._module32_first(snapshot, ctypes.byref(entry)))
            while present:
                candidate = Path(entry.szExePath).resolve()
                if _same_path(candidate, expected_executable):
                    value = ctypes.cast(
                        entry.modBaseAddr, ctypes.c_void_p
                    ).value
                    return int(value or 0)
                present = bool(
                    self._module32_next(snapshot, ctypes.byref(entry))
                )
        finally:
            self._close_handle(snapshot)
        raise AgentError(
            "startup slot0 probe could not locate the authenticated ck3.exe "
            "main module"
        )

    def exit_code(self) -> int | None:
        if self._handle is None:
            raise AgentError("startup slot0 probe reader is closed")
        code = wintypes.DWORD()
        if not self._get_exit_code_process(self._handle, ctypes.byref(code)):
            self._raise_last_error("GetExitCodeProcess")
        return None if int(code.value) == self._STILL_ACTIVE else int(code.value)

    def read_pointer(self, address: int) -> int:
        if self._handle is None:
            raise AgentError("startup slot0 probe reader is closed")
        if isinstance(address, bool) or not isinstance(address, int) or address <= 0:
            raise AgentError("startup slot0 probe read address must be positive")
        value = ctypes.c_uint64()
        transferred = ctypes.c_size_t()
        ctypes.set_last_error(0)
        if not self._read_process_memory(
            self._handle,
            ctypes.c_void_p(address),
            ctypes.byref(value),
            STARTUP_SLOT0_POINTER_BYTES,
            ctypes.byref(transferred),
        ):
            self._raise_last_error("ReadProcessMemory")
        if transferred.value != STARTUP_SLOT0_POINTER_BYTES:
            raise OSError(
                f"ReadProcessMemory returned {transferred.value} of "
                f"{STARTUP_SLOT0_POINTER_BYTES} bytes"
            )
        return int(value.value)

    def close(self) -> None:
        handle = self._handle
        self._handle = None
        if handle is not None:
            self._close_handle(handle)


@dataclass(frozen=True)
class StartupSlot0ProbePlan:
    """Prelaunch admission record for one explicitly requested probe."""

    game_exe: Path
    output_path: Path
    executable_sha256: str
    poll_interval_seconds: float
    max_duration_seconds: float

    def start(
        self,
        pid: int,
        *,
        launch_role: str,
        timeline_origin_monotonic: float | None = None,
        timeline_origin_at: str | None = None,
        reader_factory: Callable[[int, Path], _StartupSlot0Reader] = (
            WindowsStartupSlot0Reader
        ),
    ) -> "StartupSlot0ProbeController":
        controller = StartupSlot0ProbeController(
            plan=self,
            pid=pid,
            launch_role=launch_role,
            timeline_origin_monotonic=timeline_origin_monotonic,
            timeline_origin_at=timeline_origin_at,
            reader_factory=reader_factory,
        )
        controller.start()
        return controller


def prepare_startup_slot0_probe(
    game_exe: Path,
    output_path: Path,
    *,
    poll_interval_seconds: float = STARTUP_SLOT0_DEFAULT_POLL_INTERVAL_SECONDS,
    max_duration_seconds: float = STARTUP_SLOT0_DEFAULT_MAX_DURATION_SECONDS,
) -> StartupSlot0ProbePlan:
    """Fail closed before launch unless the exact executable is admitted."""

    if not isinstance(game_exe, Path) or not isinstance(output_path, Path):
        raise AgentError("startup slot0 probe paths must be pathlib.Path values")
    executable = game_exe.resolve()
    output = output_path.resolve()
    if executable.name.casefold() != "ck3.exe" or not executable.is_file():
        raise AgentError(
            f"startup slot0 probe requires an existing ck3.exe: {executable}"
        )
    for name, value in (
        ("poll interval", poll_interval_seconds),
        ("maximum duration", max_duration_seconds),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or value <= 0
        ):
            raise AgentError(f"startup slot0 probe {name} must be positive")
    temporary = output.with_name(output.name + ".tmp")
    if output.exists() or temporary.exists():
        raise AgentError(
            f"startup slot0 probe output must be new: {output}"
        )
    actual_sha256 = _sha256_file(executable)
    if actual_sha256 != EXPECTED_CK3_EXE_SHA256:
        raise AgentError(
            "startup slot0 probe exact-build gate failed: "
            f"{actual_sha256} != {EXPECTED_CK3_EXE_SHA256}"
        )
    return StartupSlot0ProbePlan(
        game_exe=executable,
        output_path=output,
        executable_sha256=actual_sha256,
        poll_interval_seconds=float(poll_interval_seconds),
        max_duration_seconds=float(max_duration_seconds),
    )


class StartupSlot0ProbeController:
    """Own one probe thread and its durable, fail-closed report."""

    def __init__(
        self,
        *,
        plan: StartupSlot0ProbePlan,
        pid: int,
        launch_role: str,
        timeline_origin_monotonic: float | None,
        timeline_origin_at: str | None,
        reader_factory: Callable[[int, Path], _StartupSlot0Reader],
        sleeper: Callable[[float], None] = time.sleep,
        monotonic: Callable[[], float] = time.monotonic,
        wall_clock: Callable[[], str] = _utc_now,
    ) -> None:
        if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
            raise AgentError("startup slot0 probe PID must be positive")
        if launch_role not in {"initial", "frontend_warmup"}:
            raise AgentError("startup slot0 probe launch role is unsupported")
        self.plan = plan
        self.pid = pid
        self.launch_role = launch_role
        self._reader_factory = reader_factory
        self._sleeper = sleeper
        self._monotonic = monotonic
        self._wall_clock = wall_clock
        self._timeline_origin_monotonic = timeline_origin_monotonic
        self._timeline_origin_at = timeline_origin_at
        self._stop_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name=f"xar-startup-slot0-probe-{pid}",
            daemon=True,
        )
        self._report_lock = threading.Lock()
        self._report: dict[str, object] | None = None

    def start(self) -> None:
        if self.plan.output_path.exists():
            raise AgentError(
                "startup slot0 probe output appeared after prelaunch admission: "
                f"{self.plan.output_path}"
            )
        self._thread.start()

    def finish(
        self, *, timeout_seconds: float = STARTUP_SLOT0_FINISH_GRACE_SECONDS
    ) -> dict[str, object]:
        """Wait for process-exit evidence, then stop without claiming success."""

        self._thread.join(timeout=max(0.0, float(timeout_seconds)))
        if self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=max(0.0, float(timeout_seconds)))
        with self._report_lock:
            report = None if self._report is None else dict(self._report)
        if report is None:
            return {
                "format_version": 1,
                "kind": "ck3_startup_slot0_timing_probe",
                "pid": self.pid,
                "capture_ok": False,
                "status": "probe_thread_unresolved",
                "errors": [
                    {
                        "stage": "controller_finish",
                        "error": "probe thread did not publish a report",
                    }
                ],
            }
        return report

    def _publish(self, report: dict[str, object]) -> None:
        with self._report_lock:
            self._report = dict(report)
        write_json_atomic(self.plan.output_path, report)

    def _run(self) -> None:
        attached_monotonic = self._monotonic()
        origin_monotonic = (
            attached_monotonic
            if self._timeline_origin_monotonic is None
            else self._timeline_origin_monotonic
        )
        report: dict[str, object] = {
            "format_version": 1,
            "kind": "ck3_startup_slot0_timing_probe",
            "claim": "read_only_startup_timing_observation_only",
            "gameplay_functionality_claimed": False,
            "map_ready_claimed": False,
            "pid": self.pid,
            "launch_role": self.launch_role,
            "status": "attaching",
            "capture_ok": False,
            "exact_build_admitted": True,
            "executable": str(self.plan.game_exe),
            "executable_sha256": self.plan.executable_sha256,
            "expected_executable_sha256": EXPECTED_CK3_EXE_SHA256,
            "root_global_rva": f"0x{STARTUP_SLOT0_ROOT_GLOBAL_RVA:X}",
            "graphics_global_rva": (
                f"0x{STARTUP_SLOT0_GRAPHICS_GLOBAL_RVA:X}"
            ),
            "manager_slot0_offset": f"0x{STARTUP_SLOT0_MANAGER_OFFSET:X}",
            "pointer_bytes": STARTUP_SLOT0_POINTER_BYTES,
            "poll_interval_seconds": self.plan.poll_interval_seconds,
            "max_duration_seconds": self.plan.max_duration_seconds,
            "timeline_origin_at": self._timeline_origin_at,
            "probe_attached_at": self._wall_clock(),
            "probe_attach_elapsed_seconds": round(
                max(0.0, attached_monotonic - origin_monotonic), 6
            ),
            "module_discovery": {
                "status": "pending",
                "retry_winerrors": sorted(
                    STARTUP_SLOT0_MODULE_DISCOVERY_RETRY_WINERRORS
                ),
                "timeout_seconds": (
                    STARTUP_SLOT0_MODULE_DISCOVERY_TIMEOUT_SECONDS
                ),
                "poll_interval_seconds": (
                    STARTUP_SLOT0_MODULE_DISCOVERY_POLL_SECONDS
                ),
                "attempts": 0,
                "transient_error_count": 0,
                "elapsed_seconds": 0.0,
                "last_winerror": None,
                "last_error": None,
                "process_exit_code": None,
            },
            "module_base": None,
            "root_global_address": None,
            "graphics_global_address": None,
            "sample_count": 0,
            "successful_root_reads": 0,
            "successful_graphics_global_reads": 0,
            "successful_slot0_reads": 0,
            "last_manager": None,
            "last_graphics_global": None,
            "last_slot0": None,
            "first_manager_nonzero": None,
            "first_graphics_global_nonzero": None,
            "first_slot0_nonzero": None,
            "process_exit": None,
            "errors": [],
            "dropped_error_count": 0,
        }

        def elapsed() -> float:
            return round(max(0.0, self._monotonic() - origin_monotonic), 6)

        def record_error(stage: str, error: BaseException) -> None:
            errors = report["errors"]
            assert isinstance(errors, list)
            row = {
                "stage": stage,
                "observed_at": self._wall_clock(),
                "elapsed_seconds": elapsed(),
                "error": f"{type(error).__name__}: {error}",
            }
            winerror = getattr(error, "winerror", None)
            if isinstance(winerror, int):
                row["winerror"] = winerror
            if len(errors) < STARTUP_SLOT0_MAX_RECORDED_ERRORS:
                errors.append(row)
            else:
                report["dropped_error_count"] = int(
                    report["dropped_error_count"]
                ) + 1

        reader: _StartupSlot0Reader | None = None
        try:
            self._publish(report)
            reader = self._reader_factory(self.pid, self.plan.game_exe)
            report["module_discovery"] = {
                "status": "ready",
                "retry_winerrors": sorted(
                    STARTUP_SLOT0_MODULE_DISCOVERY_RETRY_WINERRORS
                ),
                "timeout_seconds": (
                    STARTUP_SLOT0_MODULE_DISCOVERY_TIMEOUT_SECONDS
                ),
                "poll_interval_seconds": (
                    STARTUP_SLOT0_MODULE_DISCOVERY_POLL_SECONDS
                ),
                "attempts": int(
                    getattr(reader, "module_discovery_attempts", 1)
                ),
                "transient_error_count": int(
                    getattr(
                        reader,
                        "module_discovery_transient_error_count",
                        0,
                    )
                ),
                "elapsed_seconds": float(
                    getattr(reader, "module_discovery_elapsed_seconds", 0.0)
                ),
                "last_winerror": None,
                "last_error": None,
                "process_exit_code": None,
            }
            if not _same_path(reader.image_path, self.plan.game_exe):
                raise AgentError(
                    "startup slot0 probe reader returned a different image"
                )
            module_base = reader.module_base
            if (
                isinstance(module_base, bool)
                or not isinstance(module_base, int)
                or module_base <= 0
            ):
                raise AgentError(
                    "startup slot0 probe reader returned an invalid module base"
                )
            root_address = module_base + STARTUP_SLOT0_ROOT_GLOBAL_RVA
            graphics_global_address = (
                module_base + STARTUP_SLOT0_GRAPHICS_GLOBAL_RVA
            )
            report["module_base"] = _hex_pointer(module_base)
            report["root_global_address"] = _hex_pointer(root_address)
            report["graphics_global_address"] = _hex_pointer(
                graphics_global_address
            )
            report["status"] = "observing"
            self._publish(report)

            while True:
                exit_code = reader.exit_code()
                if exit_code is not None:
                    report["process_exit"] = {
                        "observed_at": self._wall_clock(),
                        "elapsed_seconds": elapsed(),
                        "exit_code": exit_code,
                    }
                    report["status"] = "process_exit_observed"
                    break
                if self._stop_event.is_set():
                    report["status"] = "stop_requested_before_process_exit"
                    break
                if self._monotonic() - origin_monotonic >= (
                    self.plan.max_duration_seconds
                ):
                    report["status"] = "probe_timeout_before_process_exit"
                    break

                report["sample_count"] = int(report["sample_count"]) + 1
                try:
                    graphics_global = reader.read_pointer(
                        graphics_global_address
                    )
                    report["successful_graphics_global_reads"] = int(
                        report["successful_graphics_global_reads"]
                    ) + 1
                    report["last_graphics_global"] = _hex_pointer(
                        graphics_global
                    )
                    if (
                        graphics_global != 0
                        and report["first_graphics_global_nonzero"] is None
                    ):
                        report["first_graphics_global_nonzero"] = {
                            "observed_at": self._wall_clock(),
                            "elapsed_seconds": elapsed(),
                            "address": _hex_pointer(graphics_global_address),
                            "value": _hex_pointer(graphics_global),
                        }
                        self._publish(report)
                except BaseException as error:
                    record_error("read_graphics_global", error)
                    self._publish(report)

                manager: int | None = None
                try:
                    manager = reader.read_pointer(root_address)
                    report["successful_root_reads"] = int(
                        report["successful_root_reads"]
                    ) + 1
                    report["last_manager"] = _hex_pointer(manager)
                    if (
                        manager != 0
                        and report["first_manager_nonzero"] is None
                    ):
                        report["first_manager_nonzero"] = {
                            "observed_at": self._wall_clock(),
                            "elapsed_seconds": elapsed(),
                            "value": _hex_pointer(manager),
                        }
                        self._publish(report)
                except BaseException as error:
                    record_error("read_manager_global", error)
                    self._publish(report)

                if manager:
                    slot0_address = manager + STARTUP_SLOT0_MANAGER_OFFSET
                    try:
                        slot0 = reader.read_pointer(slot0_address)
                        report["successful_slot0_reads"] = int(
                            report["successful_slot0_reads"]
                        ) + 1
                        report["last_slot0"] = _hex_pointer(slot0)
                        if (
                            slot0 != 0
                            and report["first_slot0_nonzero"] is None
                        ):
                            report["first_slot0_nonzero"] = {
                                "observed_at": self._wall_clock(),
                                "elapsed_seconds": elapsed(),
                                "address": _hex_pointer(slot0_address),
                                "value": _hex_pointer(slot0),
                            }
                            self._publish(report)
                    except BaseException as error:
                        record_error("read_manager_slot0", error)
                        self._publish(report)
                self._sleeper(self.plan.poll_interval_seconds)

            report["finished_at"] = self._wall_clock()
            report["elapsed_seconds"] = elapsed()
            report["capture_ok"] = (
                report["status"] == "process_exit_observed"
                and int(report["successful_root_reads"]) > 0
                and int(report["successful_graphics_global_reads"]) > 0
                and len(report["errors"]) == 0
                and int(report["dropped_error_count"]) == 0
            )
        except BaseException as error:
            error_stage = "probe"
            if isinstance(error, StartupSlot0ModuleDiscoveryError):
                module_discovery = error.evidence()
                module_discovery.update(
                    {
                        "retry_winerrors": sorted(
                            STARTUP_SLOT0_MODULE_DISCOVERY_RETRY_WINERRORS
                        ),
                        "timeout_seconds": (
                            STARTUP_SLOT0_MODULE_DISCOVERY_TIMEOUT_SECONDS
                        ),
                        "poll_interval_seconds": (
                            STARTUP_SLOT0_MODULE_DISCOVERY_POLL_SECONDS
                        ),
                    }
                )
                report["module_discovery"] = module_discovery
                error_stage = "module_discovery"
                if error.process_exit_code is not None:
                    report["process_exit"] = {
                        "observed_at": self._wall_clock(),
                        "elapsed_seconds": elapsed(),
                        "exit_code": error.process_exit_code,
                    }
            record_error(error_stage, error)
            report["status"] = (
                "module_discovery_process_exit"
                if isinstance(error, StartupSlot0ModuleDiscoveryError)
                and error.reason == "process_exit"
                else "module_discovery_timeout"
                if isinstance(error, StartupSlot0ModuleDiscoveryError)
                and error.reason == "timeout"
                else "probe_error"
            )
            report["capture_ok"] = False
            report["finished_at"] = self._wall_clock()
            report["elapsed_seconds"] = elapsed()
        finally:
            if reader is not None:
                try:
                    reader.close()
                except BaseException as error:
                    record_error("reader_close", error)
                    report["status"] = "probe_error"
                    report["capture_ok"] = False
            try:
                self._publish(report)
            except BaseException as error:
                # The controller can still surface this in-memory RED report.
                record_error("evidence_write", error)
                report["status"] = "probe_error"
                report["capture_ok"] = False
                with self._report_lock:
                    self._report = dict(report)
