"""Finite same-user Task Scheduler owner boundary. No production task by default.

Task -> pythonw bootstrap -> unchanged source-pinned python stage, with its own
retained process/Job and disk stdio. Task Scheduler, not tool process inheritance,
creates the bootstrap. Normal STOP forwards an exact stage marker; Task.Stop is
never used to manufacture normal closure. This is not a command broker/service.
"""
from __future__ import annotations

import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone

SCHEMA = "xar.interactive-task-owner/v1"
ROLES = {"supervisor", "display_owner", "sdk_owner", "feeder", "native_build", "fixture"}
MAX_SOURCE = 524288


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    raw = Path(path).read_bytes()
    if len(raw) > MAX_SOURCE:
        raise ValueError("owner input exceeds bounded source size")
    return hashlib.sha256(raw).hexdigest()


def once(path, body):
    """Create a new receipt; preserve all previous attempts."""
    path = Path(path)
    raw = (json.dumps(body, ensure_ascii=False, indent=2) + "\n").encode()
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".pending")
    with temporary.open("xb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    os.rename(temporary, path)  # Windows rename refuses an existing destination.


def read(path):
    raw = Path(path).read_bytes()
    if len(raw) > 65536:
        raise ValueError("owner metadata too large")
    return json.loads(raw)


def checked_spec(path, expected_sha):
    path = Path(path).resolve()
    if sha(path) != expected_sha:
        raise ValueError("owner spec SHA differs")
    s = read(path)
    if (s.get("schema") != SCHEMA or s.get("role") not in ROLES
            or not re.fullmatch(r"[0-9a-f]{32}", s.get("nonce", ""))
            or not s.get("machine_id") or not s.get("sid", "").startswith("S-1-")
            or s.get("sid") in {"S-1-5-18", "S-1-5-19", "S-1-5-20"}
            or type(s.get("session")) is not int or s["session"] <= 0):
        raise ValueError("invalid interactive owner identity")
    prefix = "XARG2ManagedOwnerFixture-" if s["role"] == "fixture" else "XARG2ManagedOwner-"
    if s.get("task_name") != prefix + s["nonce"]:
        raise ValueError("task name is not this exact finite attempt")
    for key in ("root", "cwd", "python", "pythonw", "bootstrap", "stage"):
        if not Path(s[key]).is_absolute():
            raise ValueError("owner paths must be absolute")
    if (Path(s["python"]).name.lower() != "python.exe"
            or Path(s["pythonw"]).name.lower() != "pythonw.exe"
            or Path(s["python"]).parent != Path(s["pythonw"]).parent
            or Path(s["root"]).resolve() != path.parent):
        raise ValueError("owner interpreter/root differs")
    for key in ("bootstrap", "stage"):
        if sha(s[key]) != s[key + "_sha256"]:
            raise ValueError(key + " source SHA differs")
    if any(not isinstance(s.get(k + "_file_id"), dict) for k in ("python", "pythonw")):
        raise ValueError("exact interpreter FileID required; redirector argv is not identity")
    args = s.get("stage_args")
    if not isinstance(args, list) or len(args) > 128 or any(not isinstance(a, str) or "\0" in a for a in args):
        raise ValueError("invalid finite stage arguments")
    if s["role"] == "native_build":
        admission = s.get("admission_path")
        if (not isinstance(admission, str) or not Path(admission).is_absolute()
                or sha(admission) != s.get("admission_sha256")
                or "--admission" not in args or args[args.index("--admission") + 1:] == []
                or args[args.index("--admission") + 1] != admission):
            raise ValueError("native build requires its exact separate admission and producer argv")
    if s.get("stop_path") is not None:
        stop = Path(s["stop_path"])
        if not stop.is_absolute() or not stop.name.startswith(("STOP-", "EXIT-", "fixture-stop")):
            raise ValueError("normal STOP must name an explicit stage marker")
    if not isinstance(s.get("env", {}), dict) or any(
            k not in {"PATH", "PYTHONPATH", "PYTHONDONTWRITEBYTECODE"}
            or not isinstance(v, str) or "\0" in v for k, v in s.get("env", {}).items()):
        raise ValueError("owner environment must use explicit non-secret import roots")
    return s


def action(s, spec_path, spec_sha):
    return {"path": s["pythonw"], "arguments": subprocess.list2cmdline([
        "-B", s["bootstrap"], "bootstrap", "--spec", str(Path(spec_path).resolve()),
        "--spec-sha", spec_sha]), "cwd": s["cwd"]}


class Scheduler:
    """Same-user InteractiveToken/LUA; no SYSTEM, password, triggers or retries."""
    def __init__(self):
        import pythoncom
        import win32com.client.dynamic
        pythoncom.CoInitialize()
        self.service = win32com.client.dynamic.Dispatch("Schedule.Service")
        self.service.Connect()
        self.folder = self.service.GetFolder("\\")

    def snapshot(self, name):
        task = self.folder.GetTask(name)
        d = task.Definition
        import win32security
        user = d.Principal.UserId
        if not user.startswith("S-1-"):
            sid, _, _ = win32security.LookupAccountName(None, user)
            user = win32security.ConvertSidToStringSid(sid)
        a = d.Actions.Item(1) if d.Actions.Count == 1 else None
        return {"sid": user, "logon_type": d.Principal.LogonType,
                "run_level": d.Principal.RunLevel, "actions": d.Actions.Count,
                "triggers": d.Triggers.Count, "action_type": a.Type if a else -1,
                "path": a.Path if a else None, "arguments": a.Arguments if a else None,
                "cwd": a.WorkingDirectory if a else None,
                "hidden": bool(d.Settings.Hidden), "limit": d.Settings.ExecutionTimeLimit,
                "demand": bool(d.Settings.AllowDemandStart), "multiple": d.Settings.MultipleInstances,
                "hard_terminate": bool(d.Settings.AllowHardTerminate),
                "instances": task.GetInstances(0).Count, "last_result": task.LastTaskResult}

    def absent(self, name):
        try:
            self.folder.GetTask(name)
        except Exception as e:
            # TASK not found only; access/COM failures are not absence.
            code = getattr(e, "hresult", None)
            detail = getattr(e, "excepinfo", None)
            if code == -2147352567 and isinstance(detail, tuple) and len(detail) == 6:
                code = detail[5]  # IDispatch wraps the real Win32 HRESULT.
            if code == -2147024894:
                return True
            raise
        return False

    def register(self, s, a):
        if not self.absent(s["task_name"]):
            raise FileExistsError("task already exists")
        d = self.service.NewTask(0)
        d.RegistrationInfo.Description = "Finite source-pinned CK3 project owner; no gameplay or service authority."
        d.Principal.UserId, d.Principal.LogonType, d.Principal.RunLevel = s["sid"], 3, 0
        z = d.Settings
        z.Enabled, z.Hidden, z.AllowDemandStart = True, True, True
        z.StartWhenAvailable, z.DisallowStartIfOnBatteries, z.StopIfGoingOnBatteries = False, False, False
        z.RunOnlyIfIdle, z.RunOnlyIfNetworkAvailable = False, False
        z.AllowHardTerminate, z.MultipleInstances = False, 2
        z.RestartCount = 0
        z.ExecutionTimeLimit = "PT0S"
        z.IdleSettings.StopOnIdleEnd = False
        d.Actions.Create(0)
        x = d.Actions.Item(1)
        x.Path, x.Arguments, x.WorkingDirectory = a["path"], a["arguments"], a["cwd"]
        self.folder.RegisterTaskDefinition(s["task_name"], d, 2, s["sid"], None, 3, None)

    def run(self, name):
        return self.folder.GetTask(name).Run(None).InstanceGuid

    def remove(self, name):
        self.folder.DeleteTask(name, 0)


def require_task(snapshot, s, a):
    expected = {"sid": s["sid"], "logon_type": 3, "run_level": 0,
                "actions": 1, "triggers": 0, "action_type": 0, **a,
                "hidden": True, "limit": "PT0S"}
    expected.update(demand=True, multiple=2, hard_terminate=False)
    if any(snapshot.get(k) != v for k, v in expected.items()):
        raise ValueError("actual task principal/action/settings differ")


def register(s, a, scheduler, *, allow_production=False):
    if s["role"] != "fixture" and not allow_production:
        raise ValueError("production stage registration requires separate explicit admission")
    require_caller(s, Windows().current())
    scheduler.register(s, a)
    actual = scheduler.snapshot(s["task_name"])
    require_task(actual, s, a)
    return actual


def require_caller(s, caller):
    if (caller["sid"] != s["sid"] or caller["session"] != s["session"]
            or caller["image_file_id"] != s["python_file_id"]
            or os.path.normcase(caller["image"]) != os.path.normcase(s["python"])):
        raise ValueError("task caller must be the same user/session and actual base Python image")


def prepare_spec(*, root, role, stage, stage_sha256, bootstrap_path, cwd,
                 machine_id, stage_args=(), stop_path=None, pythonpath=None,
                 admission_path=None, admission_sha256=None):
    """Create one stage spec only; does not contact/register Task Scheduler.

    Production bootstrap must be an independently admitted frozen source copy,
    so its lifetime read lease never locks the mutable repository source.
    """
    root, stage, boot = Path(root).resolve(), Path(stage).resolve(), Path(bootstrap_path).resolve()
    if role not in ROLES - {"fixture"} or sha(stage) != stage_sha256:
        raise ValueError("exact admitted production role/stage source required")
    if boot == Path(__file__).resolve() or sha(boot) != sha(__file__):
        raise ValueError("independent exact frozen bootstrap copy required")
    osapi = Windows()
    me = osapi.current()
    python = Path(me["loaded_module"]).resolve()
    if python.name.lower() != "python.exe":
        raise ValueError("prepare with actual base Python console interpreter")
    pythonw = python.with_name("pythonw.exe")
    if not pythonw.is_file():
        raise ValueError("actual base Python pythonw companion absent")
    nonce = uuid.uuid4().hex
    env = {"PYTHONDONTWRITEBYTECODE": "1"}
    if pythonpath is not None:
        env["PYTHONPATH"] = pythonpath
    spec = {"schema": SCHEMA, "role": role, "machine_id": machine_id, "nonce": nonce,
        "task_name": "XARG2ManagedOwner-" + nonce, "sid": me["sid"], "session": me["session"],
        "root": str(root), "cwd": str(Path(cwd).resolve()), "python": str(python),
        "pythonw": str(pythonw), "python_file_id": osapi.file_id(python),
        "pythonw_file_id": osapi.file_id(pythonw), "bootstrap": str(boot),
        "bootstrap_sha256": sha(boot), "stage": str(stage), "stage_sha256": stage_sha256,
        "stage_args": list(stage_args), "stop_path": str(Path(stop_path).resolve()) if stop_path else None,
        "env": env}
    if role == "native_build":
        if admission_path is None or admission_sha256 is None:
            raise ValueError("native build separate admission required")
        spec.update(admission_path=str(Path(admission_path).resolve()), admission_sha256=admission_sha256)
    root.mkdir(exist_ok=False)
    path = root / "SPEC.json"
    once(path, spec)
    digest = sha(path)
    checked_spec(path, digest)
    return {"machine_id": machine_id, "utc": now(), "spec": str(path), "spec_sha256": digest,
            "task_name": spec["task_name"], "registered": False}


class Windows:
    def __init__(self):
        if os.name != "nt":
            raise RuntimeError("Windows interactive Task owner required")
        import _winapi
        import win32api
        import win32job
        import win32process
        self.api, self.jobs, self.processes = win32api, win32job, win32process
        self.w = _winapi
        self.k = C.WinDLL("kernel32", use_last_error=True)
        self.k.GetProcessTimes.argtypes = [C.c_void_p] * 5
        self.k.GetProcessTimes.restype = C.c_int
        self.k.GetProcessId.argtypes = [C.c_void_p]
        self.k.GetProcessId.restype = C.c_uint32
        self.k.ProcessIdToSessionId.argtypes = [C.c_uint32, C.POINTER(C.c_uint32)]
        self.k.ProcessIdToSessionId.restype = C.c_int
        self.k.GetFileInformationByHandleEx.argtypes = [C.c_void_p, C.c_int, C.c_void_p, C.c_uint32]
        self.k.GetFileInformationByHandleEx.restype = C.c_int
        self.k.QueryFullProcessImageNameW.argtypes = [C.c_void_p, C.c_uint32, C.c_wchar_p, C.POINTER(C.c_uint32)]
        self.k.QueryFullProcessImageNameW.restype = C.c_int

    def file_id(self, path):
        import win32file
        class FileID(C.Structure):
            _fields_ = [("volume", C.c_uint64), ("id", C.c_ubyte * 16)]
        handle = win32file.CreateFile(str(path), 0x80, 7, None, 3, 0x80, None)
        try:
            value = FileID()
            if not self.k.GetFileInformationByHandleEx(int(handle), 18, C.byref(value), C.sizeof(value)):
                raise C.WinError(C.get_last_error())
            return {"volume_serial": str(value.volume), "file_id": bytes(value.id).hex()}
        finally:
            handle.Close()

    def identity(self, handle):
        handle = int(handle)
        times = [C.c_uint64() for _ in range(4)]
        if not self.k.GetProcessTimes(handle, *(C.byref(t) for t in times)):
            raise C.WinError(C.get_last_error())
        pid = self.k.GetProcessId(handle)
        session = C.c_uint32()
        if not pid or not self.k.ProcessIdToSessionId(pid, C.byref(session)):
            raise C.WinError(C.get_last_error())
        wait = self.w.WaitForSingleObject(handle, 0)
        if wait not in (0, 258):
            raise RuntimeError("process wait failed")
        buffer = C.create_unicode_buffer(32768)
        size = C.c_uint32(len(buffer))
        if not self.k.QueryFullProcessImageNameW(handle, 0, buffer, C.byref(size)):
            raise C.WinError(C.get_last_error())
        image = buffer.value
        return {"pid": pid, "creation_filetime": str(times[0].value),
                "image": image, "image_file_id": self.file_id(image),
                "session": session.value, "wait0": wait,
                "exit_code": self.w.GetExitCodeProcess(handle) if wait == 0 else None}

    def current(self):
        import win32security
        handle = self.api.GetCurrentProcess()
        token = win32security.OpenProcessToken(handle, 8)
        try:
            sid = win32security.ConvertSidToStringSid(win32security.GetTokenInformation(token, 1)[0])
        finally:
            token.Close()
        actual = self.identity(handle)
        loaded = self.api.GetModuleFileName(0)
        if os.path.normcase(loaded) != os.path.normcase(actual["image"]):
            raise ValueError("current loaded module and process image differ")
        return {**actual, "sid": sid, "loaded_module": loaded}

    def open(self, pid):
        return self.api.OpenProcess(0x100000 | 0x1000, False, pid)

    def close(self, handle):
        self.api.CloseHandle(handle)

    def job(self):
        job = self.jobs.CreateJobObject(None, "XARG2OwnerJob-" + uuid.uuid4().hex)
        limits = self.jobs.QueryInformationJobObject(job, self.jobs.JobObjectExtendedLimitInformation)
        limits["BasicLimitInformation"]["LimitFlags"] |= self.jobs.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        self.jobs.SetInformationJobObject(job, self.jobs.JobObjectExtendedLimitInformation, limits)
        return job

    def assign(self, job, process):
        self.jobs.AssignProcessToJobObject(job, process)
        if not self.jobs.IsProcessInJob(process, job):
            raise RuntimeError("stage not in original retained worker Job")

    def active(self, job):
        return self.jobs.QueryInformationJobObject(job, self.jobs.JobObjectBasicAccountingInformation)["ActiveProcesses"]

    def spawn(self, s):
        import msvcrt
        files = []
        try:
            files.append(open(os.devnull, "rb"))
            files.append(open(Path(s["root"]) / "stage.stdout.log", "xb"))
            files.append(open(Path(s["root"]) / "stage.stderr.log", "xb"))
            handles = [msvcrt.get_osfhandle(f.fileno()) for f in files]
            for h in handles:
                os.set_handle_inheritable(h, True)
            startup = subprocess.STARTUPINFO()
            startup.dwFlags = subprocess.STARTF_USESTDHANDLES | subprocess.STARTF_USESHOWWINDOW
            startup.wShowWindow = 0
            startup.hStdInput, startup.hStdOutput, startup.hStdError = handles
            startup.lpAttributeList = {"handle_list": handles}
            env = {**os.environ, **s.get("env", {}), "PYTHONDONTWRITEBYTECODE": "1"}
            argv = [s["python"], "-B", s["stage"], *s["stage_args"]]
            process, thread, pid, tid = self.w.CreateProcess(s["python"], subprocess.list2cmdline(argv),
                None, None, True, 0x4 | 0x08000000 | 0x00080000, env, s["cwd"], startup)
            return process, thread
        finally:
            for f in files:
                os.set_handle_inheritable(msvcrt.get_osfhandle(f.fileno()), False)
                f.close()

    def resume(self, thread):
        self.processes.ResumeThread(thread)

    def lease(self, path):
        import win32file
        return win32file.CreateFile(str(path), 0x80000000, 1, None, 3, 0x80, None)


def request_stop(s, spec_sha):
    root = Path(s["root"])
    start = read(root / "STARTED.json")
    if start.get("nonce") != s["nonce"] or start.get("spec_sha256") != spec_sha:
        raise ValueError("foreign owner STARTED")
    if not s.get("stop_path"):
        raise ValueError("stage has external normal-close contract; no marker adapter admitted")
    once(root / "STOP.json", {"nonce": s["nonce"], "spec_sha256": spec_sha,
        "child": start["child"], "requested_utc": now()})


def forward_stop(s, spec_sha, child):
    path = Path(s["root"]) / "STOP.json"
    if not path.exists():
        return False
    body = read(path)
    if (body.get("nonce") != s["nonce"] or body.get("spec_sha256") != spec_sha
            or body.get("child") != child or not s.get("stop_path")):
        raise ValueError("normal STOP binding differs")
    marker = Path(s["stop_path"])
    with marker.open("xb") as f:
        f.write(s["nonce"].encode())
        f.flush()
        os.fsync(f.fileno())
    return True


def run_owner(s, spec_sha, osapi, publish=once, *, fixture_hook=None):
    """No restart/replay: retain original child and Job until actual termination."""
    root = Path(s["root"])
    process = thread = job = None
    assigned = False
    child = None
    stop_forwarded = False
    result = {"machine_id": s["machine_id"], "nonce": s["nonce"], "spec_sha256": spec_sha}
    try:
        if any((root / name).exists() for name in ("STARTED.json", "CLOSED.json", "FAILED.json")):
            raise ValueError("owner attempt was already consumed; no stage replay")
        if s.get("stop_path") and Path(s["stop_path"]).exists():
            raise ValueError("old STOP marker exists before stage launch")
        me = osapi.current()
        if (me["sid"] != s["sid"] or me["session"] != s["session"]
                or os.path.normcase(me["image"]) != os.path.normcase(s["pythonw"])
                or me["image_file_id"] != s["pythonw_file_id"]):
            raise ValueError("bootstrap actual SID/session/image differs")
        job = osapi.job()
        process, thread = osapi.spawn(s)
        osapi.assign(job, process)  # before any original stage code runs
        assigned = True
        child = osapi.identity(process)
        if (child["wait0"] != 258 or child["session"] != s["session"]
                or os.path.normcase(child["image"]) != os.path.normcase(s["python"])
                or child["image_file_id"] != s["python_file_id"]):
            raise ValueError("actual suspended child differs")
        osapi.resume(thread)
        osapi.close(thread)
        thread = None
        publish(root / "STARTED.json", {**result, "utc": now(), "bootstrap": me,
            "child": child, "stdio": "owned disk files", "stage_source_sha256": s["stage_sha256"],
            "original_guard_contract": "unchanged; no Game/SDK/publisher success inferred"})
        while True:
            observed_wait = osapi.w.WaitForSingleObject(int(process), 50)
            if observed_wait == 0:
                break
            if observed_wait != 258:
                raise RuntimeError("retained stage wait failed")
            if fixture_hook:
                fixture_hook(osapi, process, job)
            if not stop_forwarded:
                stop_forwarded = forward_stop(s, spec_sha, child)
        code = osapi.w.GetExitCodeProcess(int(process))
        # Process image lookup can fail after exit; retained times/exit are enough.
        remaining = osapi.active(job)
        end = time.monotonic() + 2
        while remaining and time.monotonic() < end:
            time.sleep(.05)
            remaining = osapi.active(job)
        result.update(utc=now(), child=child, child_exit_code=code,
            normal_stop_forwarded=stop_forwarded, job_active_after_stage=remaining,
            forced_remaining_cleanup=remaining != 0, bootstrap_exit_code=0 if code == 0 and remaining == 0 else 1)
        publish(root / "CLOSED.json", result)
        return result["bootstrap_exit_code"]
    except BaseException as e:
        if not (root / "FAILED.json").exists():
            publish(root / "FAILED.json", {**result, "utc": now(), "error": repr(e),
                "child": child, "normal_closure_claim": False})
        return 1
    finally:
        if thread is not None:
            osapi.close(thread)
        if process is not None and not assigned and osapi.w.WaitForSingleObject(int(process), 0) == 258:
            osapi.api.TerminateProcess(process, 1)  # own still-suspended child only
            osapi.w.WaitForSingleObject(int(process), 5000)
        if job is not None:
            osapi.close(job)  # original owned Job only; failures remain forced/unknown
        if process is not None:
            osapi.close(process)


def bootstrap(spec_path, spec_sha):
    s = checked_spec(spec_path, spec_sha)
    osapi = Windows()
    leases = []
    fixture = None
    try:
        for path in (spec_path, s["bootstrap"], s["stage"]):
            leases.append(osapi.lease(path))  # READ + SHARE_READ: no write/delete through run
        if s["role"] == "native_build":
            leases.append(osapi.lease(s["admission_path"]))
        checked_spec(spec_path, spec_sha)
        if s["role"] == "fixture":
            helper = Path(__file__).with_name("qualify_interactive_task_owner_v1.py")
            if sha(helper) != s.get("fixture_helper_sha256"):
                raise ValueError("fixture helper source differs")
            leases.append(osapi.lease(helper))
            from qualify_interactive_task_owner_v1 import FixtureHook
            fixture = FixtureHook(s, osapi)
        return run_owner(s, spec_sha, osapi, fixture_hook=fixture)
    except BaseException as e:
        once(Path(s["root"]) / "BOOTSTRAP-FAILED.json", {"machine_id": s["machine_id"],
            "utc": now(), "nonce": s["nonce"], "error": repr(e), "normal_closure_claim": False})
        return 1
    finally:
        if fixture:
            fixture.close()
        for handle in leases:
            osapi.close(handle)


def main(argv=None):
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("command", choices=["prepare", "register", "run", "inspect", "stop", "unregister", "bootstrap"])
    p.add_argument("--spec", type=Path)
    p.add_argument("--spec-sha")
    p.add_argument("--allow-production", action="store_true")
    for name in ("root", "stage", "bootstrap-path", "cwd", "stop-path", "admission-path"):
        p.add_argument("--" + name, type=Path)
    for name in ("role", "stage-sha", "machine-id", "pythonpath", "admission-sha"):
        p.add_argument("--" + name)
    p.add_argument("--stage-arg", action="append", default=[])
    a = p.parse_args(argv)
    if a.command == "prepare":
        if not all((a.root, a.role, a.stage, a.stage_sha, a.bootstrap_path, a.cwd, a.machine_id)):
            p.error("prepare requires exact root/role/stage/stage-sha/bootstrap-path/cwd/machine-id")
        print(json.dumps(prepare_spec(root=a.root, role=a.role, stage=a.stage,
            stage_sha256=a.stage_sha, bootstrap_path=a.bootstrap_path, cwd=a.cwd,
            machine_id=a.machine_id, stage_args=a.stage_arg, stop_path=a.stop_path,
            pythonpath=a.pythonpath, admission_path=a.admission_path, admission_sha256=a.admission_sha)))
        return 0
    if not a.spec or not a.spec_sha:
        p.error("exact spec and spec-sha required")
    if a.command == "bootstrap":
        return bootstrap(a.spec, a.spec_sha)
    s = checked_spec(a.spec, a.spec_sha)
    require_caller(s, Windows().current())
    if a.command == "stop":
        request_stop(s, a.spec_sha)
        return 0
    scheduler = Scheduler()
    act = action(s, a.spec, a.spec_sha)
    if a.command == "register":
        actual = register(s, act, scheduler, allow_production=a.allow_production)
    else:
        actual = scheduler.snapshot(s["task_name"])
        require_task(actual, s, act)
        if a.command == "run":
            if s["role"] != "fixture" and not a.allow_production:
                raise ValueError("production stage start not separately admitted")
            actual["instance_guid"] = scheduler.run(s["task_name"])
        elif a.command == "unregister":
            if actual["instances"]:
                raise ValueError("cannot unregister a running owned task")
            scheduler.remove(s["task_name"])
            actual["absent_after"] = scheduler.absent(s["task_name"])
    print(json.dumps({"machine_id": s["machine_id"], "utc": now(), "task_name": s["task_name"],
                      "operation": a.command, "actual": actual}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
