"""One explicitly admitted harmless InteractiveToken task; never a CK3 launcher.

prepare -> launch (current caller deliberately exits73 by its own Job) -> finish.
Only two new Python actors: scheduled pythonw owner and its short harmless stage.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import uuid

import interactive_task_owner_v1 as o

MACHINE = "xenoamess-full-tower-eb9d2c1186"
WORKER = '''import pathlib,sys,time
stop,beat,nonce=pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2]),sys.argv[3]
end=time.monotonic()+90
while time.monotonic()<end:
    if stop.exists():
        raise SystemExit(0 if stop.read_text()==nonce else 51)
    with beat.open("a",encoding="ascii") as f:
        f.write("tick\\n");f.flush()
    time.sleep(.05)
raise SystemExit(54)
'''


def wait_for(path, seconds=20):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if path.exists():
            try:
                return o.read(path)
            except json.JSONDecodeError:
                pass
        time.sleep(.05)
    raise TimeoutError(str(path))


class FixtureHook:
    def __init__(self, s, osapi):
        self.s, self.api = s, osapi
        cfg = s["fixture"]
        self.tool_job = osapi.jobs.OpenJobObject(4, False, cfg["tool_job_name"])
        self.launcher = osapi.open(cfg["launcher_pid"])
        identity = osapi.identity(self.launcher)
        if (identity["creation_filetime"] != cfg["launcher_birth"]
                or identity["wait0"] != 258
                or not osapi.jobs.IsProcessInJob(self.launcher, self.tool_job)):
            raise ValueError("fixture launcher original generation/Job differs")
        self.ready, self.after = False, False

    def __call__(self, osapi, child, worker_job):
        root = Path(self.s["root"])
        checks = {"bootstrap_in_tool_job": bool(osapi.jobs.IsProcessInJob(osapi.api.GetCurrentProcess(), self.tool_job)),
                  "child_in_tool_job": bool(osapi.jobs.IsProcessInJob(child, self.tool_job)),
                  "child_in_worker_job": bool(osapi.jobs.IsProcessInJob(child, worker_job))}
        if checks != {"bootstrap_in_tool_job": False, "child_in_tool_job": False, "child_in_worker_job": True}:
            raise ValueError("real kernel Job isolation failed")
        if not self.ready:
            o.once(root / "DETACH-READY.json", {"machine_id": self.s["machine_id"], "utc": o.now(),
                **checks, "bootstrap": osapi.current(), "child": osapi.identity(child)})
            self.ready = True
        if not self.after and osapi.w.WaitForSingleObject(int(self.launcher), 0) == 0:
            code = osapi.w.GetExitCodeProcess(int(self.launcher))
            if code != 73 or osapi.active(self.tool_job) != 0:
                raise ValueError("fixture launcher was not terminated by its original Job")
            o.once(root / "DETACH-AFTER.json", {"machine_id": self.s["machine_id"], "utc": o.now(),
                **checks, "launcher_exit_code": code, "tool_job_active": 0,
                "child_wait0": osapi.w.WaitForSingleObject(int(child), 0)})
            self.after = True

    def close(self):
        self.api.close(self.launcher)
        self.api.close(self.tool_job)  # query handle only; never terminates caller Job


def prepare(root):
    root.mkdir(exist_ok=False)
    osapi = o.Windows()
    me = osapi.current()
    python = Path(me["loaded_module"]).resolve()  # actual image; never sys.executable redirector
    pythonw = python.with_name("pythonw.exe")
    if not pythonw.is_file():
        raise ValueError("base Python pythonw companion absent")
    stage = root / "harmless_stage.py"
    stage.write_text(WORKER, encoding="utf-8")
    nonce = uuid.uuid4().hex
    spec = {"schema": o.SCHEMA, "machine_id": MACHINE, "role": "fixture", "nonce": nonce,
        "task_name": "XARG2ManagedOwnerFixture-" + nonce,
        "sid": me["sid"], "session": me["session"], "root": str(root), "cwd": str(root),
        "python": str(python), "pythonw": str(pythonw),
        "python_file_id": osapi.file_id(python), "pythonw_file_id": osapi.file_id(pythonw),
        "bootstrap": str(Path(o.__file__).resolve()), "bootstrap_sha256": o.sha(o.__file__),
        "stage": str(stage), "stage_sha256": o.sha(stage),
        "stage_args": [str(root / "fixture-stop"), str(root / "heartbeat.log"), nonce],
        "stop_path": str(root / "fixture-stop"), "env": {"PYTHONDONTWRITEBYTECODE": "1"},
        "fixture_helper_sha256": o.sha(__file__)}
    o.once(root / "PREPARED.json", {"machine_id": MACHINE, "utc": o.now(), "spec_template": spec,
        "actual_caller": me, "task_registered": False})


def launch(root):
    prepared = o.read(root / "PREPARED.json")
    osapi = o.Windows()
    me = osapi.current()
    spec = prepared["spec_template"]
    if me["sid"] != spec["sid"] or me["session"] != spec["session"]:
        raise ValueError("fixture launch caller differs")
    job_name = "XARG2FixtureToolJob-" + spec["nonce"]
    tool_job = osapi.jobs.CreateJobObject(None, job_name)
    limits = osapi.jobs.QueryInformationJobObject(tool_job, osapi.jobs.JobObjectExtendedLimitInformation)
    limits["BasicLimitInformation"]["LimitFlags"] |= osapi.jobs.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    osapi.jobs.SetInformationJobObject(tool_job, osapi.jobs.JobObjectExtendedLimitInformation, limits)
    osapi.assign(tool_job, osapi.api.GetCurrentProcess())
    spec["fixture"] = {"tool_job_name": job_name, "launcher_pid": me["pid"],
                       "launcher_birth": me["creation_filetime"]}
    path = root / "SPEC.json"
    o.once(path, spec)
    digest = o.sha(path)
    s = o.checked_spec(path, digest)
    scheduler = o.Scheduler()
    act = o.action(s, path, digest)
    before = scheduler.absent(s["task_name"])
    registered = o.register(s, act, scheduler)
    o.once(root / "REGISTERED.json", {"machine_id": MACHINE, "utc": o.now(),
        "absent_before": before, "actual": registered, "spec_sha256": digest})
    instance = scheduler.run(s["task_name"])
    o.once(root / "RUN-REQUESTED.json", {"machine_id": MACHINE, "utc": o.now(), "instance_guid": instance})
    ready = wait_for(root / "DETACH-READY.json")
    o.once(root / "ABORTING-CALLER.json", {"machine_id": MACHINE, "utc": o.now(),
        "caller": me, "ready_child": ready["child"], "tool_job_self_member": True})
    sys.stdout.write("OWNED_FIXTURE_CALLER_TERMINATING_73\n")
    sys.stdout.flush()
    osapi.jobs.TerminateJobObject(tool_job, 73)  # deliberately kills only this exec fixture caller
    raise RuntimeError("TerminateJobObject did not terminate caller")


def finish(root):
    path = root / "SPEC.json"
    digest = o.sha(path)
    s = o.checked_spec(path, digest)
    after = wait_for(root / "DETACH-AFTER.json")
    start = o.read(root / "STARTED.json")
    osapi = o.Windows()
    handles = []
    actual = []
    try:
        for key in ("bootstrap", "child"):
            expected = start[key]
            handle = osapi.open(expected["pid"])
            handles.append(handle)
            observed = osapi.identity(handle)
            if (observed["creation_filetime"] != expected["creation_filetime"]
                    or observed["image_file_id"] != expected["image_file_id"] or observed["wait0"] != 258):
                raise ValueError("fresh original Task actor not live after caller Job abort")
            actual.append(observed)
        beat = root / "heartbeat.log"
        before = beat.stat().st_size if beat.exists() else 0
        time.sleep(.2)
        advanced = beat.stat().st_size > before
        if not advanced:
            raise ValueError("harmless child did not continue after tool caller abort")
        o.request_stop(s, digest)
        closed = wait_for(root / "CLOSED.json")
        if closed.get("child_exit_code") != 0 or closed.get("forced_remaining_cleanup") is not False:
            raise ValueError("normal worker STOP not proven")
        exits = []
        for handle in handles:
            if osapi.w.WaitForSingleObject(int(handle), 5000) != 0:
                raise ValueError("Task actor did not finish")
            exits.append(osapi.w.GetExitCodeProcess(int(handle)))
        if exits != [0, 0]:
            raise ValueError("actual Task actor exits are not both0")
        scheduler = o.Scheduler()
        end = time.monotonic() + 10
        while scheduler.snapshot(s["task_name"])["instances"] and time.monotonic() < end:
            time.sleep(.05)
        final = scheduler.snapshot(s["task_name"])
        o.require_task(final, s, o.action(s, path, digest))
        if final["instances"] or final["last_result"] != 0:
            raise ValueError("actual registered task not normally closed")
        scheduler.remove(s["task_name"])
        absent = scheduler.absent(s["task_name"])
        o.once(root / "RESULT.json", {"machine_id": MACHINE, "utc": o.now(), "status": "PASS_OWNED_MECHANICS_ONLY",
            "spec_sha256": digest, "actual_actor_identity_after_abort": actual, "actual_exit_codes": exits,
            "post_tool_job": after, "heartbeat_advanced_after_abort": advanced,
            "task_definition_after": final, "exact_task_absent_after": absent,
            "Game_OBS_desktop_input_calls": 0, "production_stage_qualification": False,
            "source_pins": {"bootstrap": o.sha(o.__file__), "fixture": o.sha(__file__)}})
    finally:
        for handle in handles:
            osapi.close(handle)


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument("phase", choices=["prepare", "launch", "finish"])
    p.add_argument("--root", type=Path, required=True)
    a = p.parse_args()
    root = a.root.resolve()
    if not root.name.startswith("m0-managed-owner-fixture-"):
        raise ValueError("fixture root prefix required")
    globals()[a.phase](root)


if __name__ == "__main__":
    main()
