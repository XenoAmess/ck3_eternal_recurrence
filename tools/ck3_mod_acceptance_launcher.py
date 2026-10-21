"""Launch one frozen shared host after a fresh background Steam observation.

The detached supervisor retains the real host Popen. Its exit receipt is host
process evidence only; product acceptance and normal CK3 exit remain separate.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
from collections.abc import Sequence
from ck3_mod_acceptance_background_types import (JsonObject, ProcessGeneration, json_object,
    text_field, object_field, strings_field, environment, process_handle, keyed_file_pin,
    CONTROL_QUEUE_MODULE_ORDER_V1)
from ck3_mod_acceptance_steam_gate import OfflineAdmission

from ck3_mod_acceptance_keeper import check_pin, live_lease, pin, read_json, require, utc, write_new

MAX_REVIEW_AGE = 600


def recent(timestamp: str, *, now: datetime | None = None) -> datetime:
    instant = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    now = now or datetime.now(timezone.utc)
    require(instant.tzinfo is not None and 0 <= (now - instant).total_seconds() <= MAX_REVIEW_AGE,
            "Direct review/challenge/Steam frame is stale or from the future")
    return instant


def frozen_run(run_root: Path, *, all_pins: bool = True, input_phase: str = "launch") -> tuple[JsonObject, JsonObject]:
    root = Path(run_root).resolve()
    frozen_path = root / "frozen-argv.json"
    frozen = json_object(read_json(frozen_path))
    argv = strings_field(frozen, "argv")
    require(bool(text_field(frozen,"run_id")) and bool(argv), "Actual frozen run/argv required")
    require(frozen.get("launch_requires_fresh_owned_cas_and_background_offline") is True,
            "Allocated background offline gate is missing")
    if frozen.get('initial_machine_no_predecessor') is True:
        fresh_helper = Path(__file__).with_name('ck3_mod_acceptance_fresh_machine_bootstrap.py').resolve()
        fresh_files = object_field(frozen, 'files')
        require(str(fresh_helper) in fresh_files, 'Fresh-machine helper absent from actual allocation pins')
        check_pin(keyed_file_pin(str(fresh_helper), fresh_files[str(fresh_helper)]))
        from ck3_mod_acceptance_fresh_machine_bootstrap import validate_frozen_fresh_admission
        validate_frozen_fresh_admission(frozen, root)
    else:
        require(frozen.get("previous_session_closed") is True and frozen.get("previous_screen_released") is True,
                "Previous managed session/screen closure is not admitted")
    context = json_object(read_json(root / "ready-context.json"))
    context_pin = object_field(context,"frozen_argv")
    check_pin(context_pin)
    require(Path(text_field(context_pin,"path")).resolve() == frozen_path and
            context.get("run_id") == frozen["run_id"] and Path(text_field(context,"run_dir")).resolve() == root,
            "Ready allocation does not bind this exact frozen argv")
    files = object_field(frozen,"files")
    require(isinstance(files, dict) and files, "Allocated exact input pins required")
    require(input_phase in {"launch", "running"}, "Unknown frozen input phase")
    if all_pins:
        if input_phase == "running":
            import importlib.util
            source = Path(__file__).with_name("ck3_mod_acceptance_runtime_inputs.py").resolve()
            require(str(source) in files, "Running input helper is absent from allocation pins")
            check_pin(keyed_file_pin(str(source), files[str(source)]))
            spec = importlib.util.spec_from_file_location("shared_acceptance_runtime_inputs", source)
            if spec is None or spec.loader is None:raise ValueError("Running input loader unavailable")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            frozen["_runtime_input_observation"] = json_object(module.validate_running_inputs(root, frozen))
        else:
            for name, row in files.items():
                check_pin(keyed_file_pin(name, row))
        check_pin(frozen["runtime_manifest"])
    # A copied helper must not silently import another unpinned sibling.
    for name in CONTROL_QUEUE_MODULE_ORDER_V1:
        path = Path(__file__).with_name(name+'.py').resolve()
        require(str(path) in files, "Public helper is absent from allocation pins: " + str(path))
        check_pin(keyed_file_pin(str(path), files[str(path)]))
    host = str(Path(argv[argv.index("--agent-source-root") - 1]).resolve())
    require(host in files, "Actual shared host is absent from allocation pins")
    check_pin(keyed_file_pin(host, files[host]))
    frozen["_checked_frozen_argv"] = json_object(pin(frozen_path))
    return frozen, context








def admission(args: argparse.Namespace) -> tuple[JsonObject, OfflineAdmission, JsonObject]:
    root = args.run_root.resolve()
    frozen, context = frozen_run(root)
    require(Path(text_field(context,"keeper_root")).resolve() == args.keeper_root.resolve(), "Wrong allocated keeper")
    from ck3_mod_acceptance_steam_gate import validate_receipt
    from steam_offline_state_probe import WindowsReader
    from ck3_live_run_id import current_machine_id
    machine=current_machine_id()
    require(object_field(frozen,'identity_allocation').get('machine_id')==machine,'Frozen machine differs')
    review=validate_receipt(args.steam_offline_receipt,machine_id=machine,reader=WindowsReader())
    owner = json_object(live_lease(args.keeper_root, frozen))
    import psutil
    require(not any((row.info["name"] or "").lower() == "ck3.exe" for row in psutil.process_iter(["name"])),
            "CK3 is already running")
    expected_environment = environment(frozen.get("runtime_environment", {}))
    argv = strings_field(frozen,"argv")
    require(all(os.environ.get(name) == value for name, value in expected_environment.items()),
            "Actual host import environment differs from frozen shared runtime")
    require("--output" in argv and
            Path(argv[argv.index("--output") + 1]).resolve() == root / "native-report.json",
            "Host output differs from actual allocation")
    return frozen, review, owner


def retain_host(root: Path, frozen: JsonObject, review: OfflineAdmission, owner: JsonObject) -> int:
    """Retain one actual Popen until wait returns; useful with harmless test children."""
    root = Path(root).resolve()
    require(not (root / "host-started.json").exists(), "Shared host launch already consumed")
    from ck3_mod_acceptance_steam_gate import recheck_before_popen
    from steam_offline_state_probe import WindowsReader
    recheck_before_popen(review,reader=WindowsReader())
    stdout = (root / "host-stdout.log").open("xb")
    stderr = (root / "host-stderr.log").open("xb")
    child = None
    try:
        child = subprocess.Popen(strings_field(frozen,"argv"), cwd=text_field(frozen,"lease_anchor"), stdout=stdout, stderr=stderr)
        import psutil
        try:
            creation = psutil.Process(child.pid).create_time()
        except psutil.NoSuchProcess:
            creation = None  # A quick real child can already be waitable.
        write_new(root / "host-started.json", {"at_utc": utc(), "pid": child.pid,
            "create_time": creation, "supervisor_pid": os.getpid(),
            "argv": frozen["argv"], "run_id": frozen["run_id"], "admitted_lease": owner["lease"],
            "background_offline_admission": review, "actual_popen_retained": True, "business_pass": False})
        code = child.wait()
        write_new(root / "host-original-process-exit.json", {"at_utc": utc(), "pid": child.pid,
            "returncode": code, "run_id": frozen["run_id"], "actual_original_popen_wait": True,
            "normal_ck3_exit_inferred": False, "business_pass": False})
        return 0 if code == 0 else 1
    finally:
        # If recording the start fails after CreateProcess, keep the original
        # handle alive until that same child exits. Never turn a lost parent
        # observation into an invented process-gone/exit0 receipt.
        if child is not None and not (root / "host-original-process-exit.json").exists():
            code = child.wait()
            write_new(root / "host-original-process-exit.json", {"at_utc": utc(), "pid": child.pid,
                "returncode": code, "run_id": frozen["run_id"], "actual_original_popen_wait": True,
                "normal_ck3_exit_inferred": False, "business_pass": False,
                "start_recording_failed": True})
        stdout.close(); stderr.close()


def _birth_filetime(handle: int) -> str:
    import ctypes
    from ctypes import wintypes
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetProcessTimes.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(wintypes.FILETIME)]*4
    kernel.GetProcessTimes.restype=wintypes.BOOL
    fields=[wintypes.FILETIME() for _ in range(4)]
    require(kernel.GetProcessTimes(handle,*[ctypes.byref(f) for f in fields]),'Exact original process creation unavailable')
    value=(fields[0].dwHighDateTime<<32)|fields[0].dwLowDateTime
    require(value>0,'Exact process creation is empty')
    return str(value)


def process_identity(pid: int) -> ProcessGeneration:
    import ctypes
    from ctypes import wintypes
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.OpenProcess(0x1000,False,pid)
    require(handle,'Known supervisor process identity unavailable')
    try:return {'pid':pid,'birth_filetime':_birth_filetime(handle)}
    finally:kernel.CloseHandle(handle)


def supervise(args: argparse.Namespace) -> int:
    root = args.run_root.resolve()
    intent = read_json(root / "launch-intent.json")
    require(intent.get("ticket") == args.launch_ticket, "Original once-only launcher ticket differs")
    require(intent.get('schema')=='ck3-mod-acceptance-background-launch-intent-v1','Background intent schema required')
    check_pin(intent['steam_offline_receipt']); check_pin(intent['frozen_argv'])
    require(Path(intent['steam_offline_receipt']['path']).resolve()==args.steam_offline_receipt.resolve(),'Receipt crossed original intent')
    from ck3_mod_acceptance_steam_gate import BackgroundGateRefusal
    try:
        frozen, review, owner = admission(args)
        require(review['receipt']==intent['steam_offline_receipt'] and intent['frozen_argv']==pin(root/'frozen-argv.json'),'Original background admission changed')
        return retain_host(root, frozen, review, owner)
    except BackgroundGateRefusal as error:
        frozen,_ = frozen_run(root)
        write_new(root/'supervisor-background-refused.json', {
            'schema':'ck3-mod-acceptance-background-supervisor-prehost-refusal-v1',
            'machine_id':text_field(object_field(frozen,'identity_allocation'),'machine_id'),'at_utc':utc(),
            'run_id':frozen['run_id'],'supervisor_pid':os.getpid(),
            'runtime_identity':process_identity(os.getpid()),'runtime_parent_identity':process_identity(os.getppid()),
            'stage':'BACKGROUND_ADMISSION_BEFORE_RETAIN_HOST',
            'reason_code':error.reason_code,'error_type':type(error).__name__,
            'error_repr':repr(error),'launch_intent':pin(root/'launch-intent.json'),
            'frozen_argv':pin(root/'frozen-argv.json'),'steam_offline_receipt':intent['steam_offline_receipt'],
            'host_started':False,'game_started':False,'native_session_started':False,'business_pass':False})
        raise



def launch(args: argparse.Namespace) -> int:
    root = args.run_root.resolve()
    frozen, review, owner = admission(args)
    require(not (root / "launch-intent.json").exists(), "Original launch intent already consumed; never replay")
    ticket = secrets.token_hex(32)
    write_new(root / "launch-intent.json", {'schema':'ck3-mod-acceptance-background-launch-intent-v1',
        'at_utc':utc(),'ticket':ticket,'run_id':frozen['run_id'],
        'steam_offline_receipt':review['receipt'],'background_admission':review,'frozen_argv':pin(root/'frozen-argv.json'),
        "admitted_lease": owner["lease"], "business_pass": False})
    argv = [sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()),
            "--run-root", str(root), "--keeper-root", str(args.keeper_root.resolve()),
            '--steam-offline-receipt',str(args.steam_offline_receipt.resolve()),
            "--supervise", "--launch-ticket", ticket]
    with (root / "host-supervisor-stdout.log").open("xb") as stdout, (root / "host-supervisor-stderr.log").open("xb") as stderr:
        child = subprocess.Popen(argv, cwd=text_field(frozen,"lease_anchor"), stdout=stdout, stderr=stderr,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    original_identity=None
    handed_off=False
    original_waited=False
    try:
        original_identity={'pid':child.pid,'birth_filetime':_birth_filetime(process_handle(child))}
        write_new(root / "host-supervisor-started.json", {"at_utc": utc(), "pid": child.pid, "argv": argv,
            "machine_id":text_field(object_field(frozen,"identity_allocation"),"machine_id"),"original_popen_identity":original_identity,
            "business_pass": False})
        deadline = time.monotonic() + 45
        start_read_error = None
        while time.monotonic() < deadline:
            if (root / "host-started.json").exists():
                try:
                    host = read_json(root / "host-started.json")
                except json.JSONDecodeError as error:
                    start_read_error = error
                else:
                    handed_off=True  # Only the original supervisor's actual host ACK transfers custody.
                    print(json.dumps({"status":"ORIGINAL_SHARED_HOST_STARTED","run_id":frozen["run_id"],
                        "host":host,"business_pass":False}),flush=True)
                    return 0
            if child.poll() is not None:
                code=child.wait()
                original_waited=True
                write_new(root/'host-supervisor-original-wait.json',{
                    'machine_id':text_field(object_field(frozen,'identity_allocation'),'machine_id'),'at_utc':utc(),
                    'run_id':frozen['run_id'],'pid':child.pid,'returncode':code,'original_popen_identity':original_identity,
                    'actual_original_popen_wait':True,'supervisor_started':pin(root/'host-supervisor-started.json'),
                    'launch_intent':pin(root/'launch-intent.json'),'business_pass':False})
                raise ValueError('Original host supervisor refused before host; original wait recorded; never replay')
            time.sleep(.05)
        raise TimeoutError("Original host supervisor launch not proved in budget; never replay") from start_read_error
    finally:
        if not handed_off and not original_waited:
            # A fallible creation/read/write or diagnostic timeout never abandons
            # the actual Popen. Keep this CLI alive; no kill, spawn or SDK replay.
            while True:
                try:
                    code=child.wait(timeout=1)
                    break
                except subprocess.TimeoutExpired:
                    continue
                except BaseException:
                    try:time.sleep(.05)
                    except BaseException:pass
            path=root/'host-supervisor-original-wait.json'
            if not path.exists():
                write_new(path,{'machine_id':text_field(object_field(frozen,'identity_allocation'),'machine_id'),'at_utc':utc(),
                    'run_id':frozen['run_id'],'pid':child.pid,'returncode':code,
                    'original_popen_identity':original_identity,'actual_original_popen_wait':True,
                    'launch_intent':pin(root/'launch-intent.json'),
                    'start_recording_or_ack_failed':True,'business_pass':False})



def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--keeper-root", required=True, type=Path)
    parser.add_argument('--steam-offline-receipt',type=Path,required=True)
    parser.add_argument("--supervise", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--launch-ticket", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        return supervise(args) if args.supervise else launch(args)
    except Exception as error:
        print(json.dumps({"status": "BLOCKED", "error": repr(error), "business_pass": False}), file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
