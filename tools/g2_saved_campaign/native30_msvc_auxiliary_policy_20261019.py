"""Explicit owned compiler-server cleanup after a retained command exits zero."""
import ctypes as C
import hashlib
import os
from pathlib import Path
import time

AUXILIARIES = ("vctip.exe", "mspdbsrv.exe")

class AuxiliaryContractError(RuntimeError):
    pass

def same_image(actual, expected):
    return (os.path.normcase(actual["canonical_path"]) == os.path.normcase(expected["canonical_path"])
            and actual["file_id"] == expected["file_id"] and actual["sha256"] == expected["sha256"])

class WindowsFiles:
    def __init__(self):
        self.k = C.WinDLL("kernel32", use_last_error=True)
        k = self.k
        k.CreateFileW.argtypes = [C.c_wchar_p, C.c_uint32, C.c_uint32, C.c_void_p, C.c_uint32, C.c_uint32, C.c_void_p]
        k.CreateFileW.restype = C.c_void_p
        k.CloseHandle.argtypes, k.CloseHandle.restype = [C.c_void_p], C.c_int
        k.GetFileInformationByHandleEx.argtypes = [C.c_void_p, C.c_int, C.c_void_p, C.c_uint32]
        k.GetFileInformationByHandleEx.restype = C.c_int
        k.GetFinalPathNameByHandleW.argtypes = [C.c_void_p, C.c_wchar_p, C.c_uint32, C.c_uint32]
        k.GetFinalPathNameByHandleW.restype = C.c_uint32
        k.ReadFile.argtypes = [C.c_void_p, C.c_void_p, C.c_uint32, C.POINTER(C.c_uint32), C.c_void_p]
        k.ReadFile.restype = C.c_int
        k.GetProcessTimes.argtypes, k.GetProcessTimes.restype = [C.c_void_p] * 5, C.c_int
        k.QueryFullProcessImageNameW.argtypes = [C.c_void_p, C.c_uint32, C.c_wchar_p, C.POINTER(C.c_uint32)]
        k.QueryFullProcessImageNameW.restype = C.c_int
        k.GetProcessId.argtypes, k.GetProcessId.restype = [C.c_void_p], C.c_uint32
        k.QueryInformationJobObject.argtypes = [C.c_void_p, C.c_uint32, C.c_void_p, C.c_uint32, C.POINTER(C.c_uint32)]
        k.QueryInformationJobObject.restype = C.c_int

    def file(self, path):
        class FileID(C.Structure):
            _fields_ = [("volume", C.c_uint64), ("value", C.c_ubyte * 16)]
        # One read handle binds path, file ID and digest; writers/replacement cannot
        # race this identity read. This is a file check, never a process launch.
        handle = self.k.CreateFileW(str(path), 0x80000080, 1, None, 3, 0x80, None)
        if handle == C.c_void_p(-1).value: raise C.WinError(C.get_last_error())
        try:
            identity = FileID()
            if not self.k.GetFileInformationByHandleEx(handle, 18, C.byref(identity), C.sizeof(identity)):
                raise C.WinError(C.get_last_error())
            full = C.create_unicode_buffer(32768)
            count = self.k.GetFinalPathNameByHandleW(handle, full, len(full), 0)
            if not 0 < count < len(full): raise AuxiliaryContractError("canonical tool path unavailable")
            digest, buffer, count_read = hashlib.sha256(), C.create_string_buffer(1048576), C.c_uint32()
            total = 0
            while True:
                if not self.k.ReadFile(handle, buffer, len(buffer), C.byref(count_read), None):
                    raise C.WinError(C.get_last_error())
                if not count_read.value: break
                total += count_read.value
                if total > 64 * 1048576: raise AuxiliaryContractError("tool image read bound")
                digest.update(buffer.raw[:count_read.value])
            canonical = full.value
            if canonical.startswith("\\\\?\\"): canonical = canonical[4:]
            return {"canonical_path": canonical, "file_id": {"volume_serial": str(identity.volume),
                    "file_id": bytes(identity.value).hex()}, "sha256": digest.hexdigest(), "bytes": total}
        finally:
            self.k.CloseHandle(handle)

    def process(self, handle):
        handle = int(handle)
        times = [C.c_uint64() for _ in range(4)]
        if not self.k.GetProcessTimes(handle, *(C.byref(value) for value in times)):
            raise C.WinError(C.get_last_error())
        image, length = C.create_unicode_buffer(32768), C.c_uint32(32768)
        if not self.k.QueryFullProcessImageNameW(handle, 0, image, C.byref(length)):
            raise C.WinError(C.get_last_error())
        return {"pid": self.k.GetProcessId(handle), "creation_filetime": str(times[0].value),
                "image": self.file(image.value)}

def bind_auxiliaries(compiler):
    files = WindowsFiles()
    cl = files.file(compiler)
    directory = Path(cl["canonical_path"]).parent
    result = {name: files.file(directory / name) for name in AUXILIARIES}
    if any(Path(row["canonical_path"]).parent != directory for row in result.values()):
        raise AuxiliaryContractError("compiler auxiliary is outside the exact compiler directory")
    return {"compiler": cl, "auxiliaries": result}

class OwnedBackend:
    """Read/terminate handles only from this newly created job's own member list."""
    def __init__(self, process):
        import win32api, win32job, win32event
        self.process, self.api, self.jobs, self.event = process, win32api, win32job, win32event
        self.files = WindowsFiles()
    def root_wait(self): return self.event.WaitForSingleObject(self.process.process, 0)
    def root_exit(self): return self.process.processapi.GetExitCodeProcess(self.process.process)
    def active(self): return self.process.active()
    def members(self):
        buffer, needed = C.create_string_buffer(8 + 64 * C.sizeof(C.c_size_t)), C.c_uint32()
        if not self.files.k.QueryInformationJobObject(int(self.process.job), 3, buffer, len(buffer), C.byref(needed)):
            raise C.WinError(C.get_last_error())
        assigned, listed = (C.c_uint32 * 2).from_buffer(buffer)
        if listed != assigned or listed > 16: raise AuxiliaryContractError("owned auxiliary count/incomplete list")
        return list((C.c_size_t * listed).from_buffer(buffer, 8))
    def open(self, pid): return self.api.OpenProcess(0x100000 | 0x1000 | 1, False, pid)
    def identity(self, handle): return self.files.process(handle)
    def belongs(self, handle): return self.jobs.IsProcessInJob(handle, self.process.job)
    def wait(self, handle, milliseconds): return self.event.WaitForSingleObject(handle, milliseconds)
    def terminate(self, handle): self.api.TerminateProcess(handle, 74)
    def exit_code(self, handle): return self.process.processapi.GetExitCodeProcess(handle)
    def close(self, handle): handle.Close()

def finish_command(backend, binding, guard, *, grace_seconds=1.0, cleanup_seconds=5.0,
                   clock=time.monotonic, sleep=time.sleep, state=None):
    """Root exit and allowed auxiliary cleanup remain distinct recorded facts."""
    if backend.root_wait() != 0: raise AuxiliaryContractError("retained command has not exited")
    root_code = backend.root_exit()
    if root_code != 0: raise AuxiliaryContractError("original command exit " + str(root_code))
    grace_end = clock() + grace_seconds
    while backend.active() and clock() < grace_end:
        guard()
        sleep(.05)
    report = state if state is not None else {}
    report.update(original_root_exit_code=root_code, auxiliary_policy="exact-msvc-owned-after-root-zero-v1",
                  auxiliary_forced_cleanup=[], owned_active_after=None)
    if not backend.active():
        report["owned_active_after"] = 0
        return report
    retained = []
    try:
        # Validate the complete finite set before ending even one member.
        pids = backend.members()
        if not pids or len(pids) > 16: raise AuxiliaryContractError("unknown owned member set")
        for pid in pids:
            handle = backend.open(pid)
            retained.append((handle, None))
            if not backend.belongs(handle) or backend.wait(handle, 0) != 258:
                raise AuxiliaryContractError("member exited or is outside exact owned job")
            actual = backend.identity(handle)
            matched = [name for name, image in binding["auxiliaries"].items() if same_image(actual["image"], image)]
            if actual["pid"] != pid or len(matched) != 1:
                raise AuxiliaryContractError("unknown/nonidentical owned process; no auxiliary cleanup")
            retained[-1] = (handle, {**actual, "tool": matched[0]})
        # A process handle fixes birth identity; recheck membership immediately
        # before termination. No PID reopening and no Job-wide successful cleanup.
        for handle, row in retained:
            if not backend.belongs(handle) or backend.wait(handle, 0) != 258:
                raise AuxiliaryContractError("member identity/membership changed before cleanup")
            backend.terminate(handle)
            report["auxiliary_forced_cleanup"].append(row)
        end = clock() + cleanup_seconds
        while backend.active() and clock() < end:
            guard()
            sleep(.05)
        if backend.active(): raise AuxiliaryContractError("owned members remain after exact auxiliary cleanup")
        if backend.members(): raise AuxiliaryContractError("new/unknown member appeared after cleanup")
        for handle, row in retained:
            if backend.wait(handle, 0) != 0: raise AuxiliaryContractError("terminated auxiliary handle not signaled")
            row["actual_exit_code"] = backend.exit_code(handle)
        report["owned_active_after"] = 0
        return report
    finally:
        for handle, _ in retained: backend.close(handle)

def run_owned(base, argv, cwd, environment, log, guard, binding, timeout=1800, reserve=64*1048576,
              state=None):
    guard(reserve)
    started, clock = base.utc(), time.monotonic()
    process = base.OwnedJob(argv, cwd, environment, log)
    backend = None
    report = state if state is not None else {}
    report.update(auxiliary_forced_cleanup=[], failure_job_termination=False, owned_active_after=None,
                  argv=argv, pid=process.pid, start_utc=started)
    journal = log.with_name(log.name + ".auxiliary.json")
    try:
        backend = OwnedBackend(process)
        while backend.root_wait() == 258:
            guard()
            if time.monotonic() - clock >= timeout: raise AuxiliaryContractError("owned command timeout")
            time.sleep(.25)
        finish_command(backend, binding, guard, state=report)
        process.wait_root()
        guard()
        return {"argv": argv, "pid": process.pid, "start_utc": started, "end_utc": base.utc(),
                "returncode": report["original_root_exit_code"], "owned_active_after": 0,
                "auxiliary_cleanup": report, "log": base.pin(log)}
    except BaseException as error:
        report["error"] = repr(error)
        report["failure_job_termination"] = True
        process.stop()  # Failure-only termination of this exact original Job.
        raise
    finally:
        try:
            report.update(end_utc=base.utc(),
                          original_root_exit_code=process.processapi.GetExitCodeProcess(process.process),
                          owned_active_after=process.active())
            base.write(journal, report)
        finally:
            process.close()
