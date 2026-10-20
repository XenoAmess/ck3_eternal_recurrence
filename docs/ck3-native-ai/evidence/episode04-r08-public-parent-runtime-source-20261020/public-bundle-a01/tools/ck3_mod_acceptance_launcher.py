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

from ck3_mod_acceptance_keeper import check_pin, live_lease, pin, read_json, require, utc, write_new

MAX_REVIEW_AGE = 600


def recent(timestamp, *, now=None):
    instant = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    now = now or datetime.now(timezone.utc)
    require(instant.tzinfo is not None and 0 <= (now - instant).total_seconds() <= MAX_REVIEW_AGE,
            "Direct review/challenge/Steam frame is stale or from the future")
    return instant


def frozen_run(run_root, *, all_pins=True, input_phase="launch"):
    root = Path(run_root).resolve()
    frozen_path = root / "frozen-argv.json"
    frozen = read_json(frozen_path)
    require(isinstance(frozen.get("run_id"), str) and frozen["run_id"] and
            isinstance(frozen.get("argv"), list) and frozen["argv"] and
            all(isinstance(arg, str) and arg for arg in frozen["argv"]), "Actual frozen run/argv required")
    require(frozen.get("launch_requires_fresh_owned_cas_and_background_offline") is True,
            "Allocated background offline gate is missing")
    require(frozen.get("previous_session_closed") is True and frozen.get("previous_screen_released") is True,
            "Previous managed session/screen closure is not admitted")
    context = read_json(root / "ready-context.json")
    check_pin(context["frozen_argv"])
    require(Path(context["frozen_argv"]["path"]).resolve() == frozen_path and
            context.get("run_id") == frozen["run_id"] and Path(context["run_dir"]).resolve() == root,
            "Ready allocation does not bind this exact frozen argv")
    files = frozen.get("files")
    require(isinstance(files, dict) and files, "Allocated exact input pins required")
    require(input_phase in {"launch", "running"}, "Unknown frozen input phase")
    if all_pins:
        if input_phase == "running":
            import importlib.util
            source = Path(__file__).with_name("ck3_mod_acceptance_runtime_inputs.py").resolve()
            require(str(source) in files, "Running input helper is absent from allocation pins")
            check_pin({**files[str(source)], "path": str(source)})
            spec = importlib.util.spec_from_file_location("shared_acceptance_runtime_inputs", source)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            frozen["_runtime_input_observation"] = module.validate_running_inputs(root, frozen)
        else:
            for name, row in files.items():
                check_pin({**row, "path": name})
        check_pin(frozen["runtime_manifest"])
    # A copied helper must not silently import another unpinned sibling.
    for name in ("ck3_mod_acceptance_launcher.py", "ck3_mod_acceptance_keeper.py", "ck3_mod_acceptance_queue.py", "ck3_mod_acceptance_steam_gate.py", "steam_offline_state_contract.py", "steam_offline_state_probe.py", "steam_offline_native_provider_v1.py", "ck3_live_run_id.py"):
        path = Path(__file__).with_name(name).resolve()
        require(str(path) in files, "Public helper is absent from allocation pins: " + str(path))
        check_pin({**files[str(path)], "path": str(path)})
    host = str(Path(frozen["argv"][frozen["argv"].index("--agent-source-root") - 1]).resolve())
    require(host in files, "Actual shared host is absent from allocation pins")
    check_pin({**files[host], "path": host})
    frozen["_checked_frozen_argv"] = pin(frozen_path)
    return frozen, context








def admission(args):
    root = args.run_root.resolve()
    frozen, context = frozen_run(root)
    require(Path(context["keeper_root"]).resolve() == args.keeper_root.resolve(), "Wrong allocated keeper")
    from ck3_mod_acceptance_steam_gate import validate_receipt
    from steam_offline_state_probe import WindowsReader
    from ck3_live_run_id import current_machine_id
    machine=current_machine_id()
    require(frozen.get('identity_allocation',{}).get('machine_id')==machine,'Frozen machine differs')
    review=validate_receipt(args.steam_offline_receipt,machine_id=machine,reader=WindowsReader())
    owner = live_lease(args.keeper_root, frozen)
    import psutil
    require(not any((row.info["name"] or "").lower() == "ck3.exe" for row in psutil.process_iter(["name"])),
            "CK3 is already running")
    expected_environment = frozen.get("runtime_environment", {})
    require(all(os.environ.get(name) == value for name, value in expected_environment.items()),
            "Actual host import environment differs from frozen shared runtime")
    require("--output" in frozen["argv"] and
            Path(frozen["argv"][frozen["argv"].index("--output") + 1]).resolve() == root / "native-report.json",
            "Host output differs from actual allocation")
    return frozen, review, owner


def retain_host(root, frozen, review, owner):
    """Retain one actual Popen until wait returns; useful with harmless test children."""
    root = Path(root).resolve()
    require(not (root / "host-started.json").exists(), "Shared host launch already consumed")
    stdout = (root / "host-stdout.log").open("xb")
    stderr = (root / "host-stderr.log").open("xb")
    child = None
    try:
        from ck3_mod_acceptance_steam_gate import recheck_before_popen
        from steam_offline_state_probe import WindowsReader
        recheck_before_popen(review,reader=WindowsReader())
        child = subprocess.Popen(frozen["argv"], cwd=frozen["lease_anchor"], stdout=stdout, stderr=stderr)
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


def supervise(args):
    root = args.run_root.resolve()
    intent = read_json(root / "launch-intent.json")
    require(intent.get("ticket") == args.launch_ticket, "Original once-only launcher ticket differs")
    require(intent.get('schema')=='ck3-mod-acceptance-background-launch-intent-v1','Background intent schema required')
    check_pin(intent['steam_offline_receipt']); check_pin(intent['frozen_argv'])
    require(Path(intent['steam_offline_receipt']['path']).resolve()==args.steam_offline_receipt.resolve(),'Receipt crossed original intent')
    frozen, review, owner = admission(args)
    require(review['receipt']==intent['steam_offline_receipt'] and intent['frozen_argv']==pin(root/'frozen-argv.json'),'Original background admission changed')
    return retain_host(root, frozen, review, owner)


def launch(args):
    root = args.run_root.resolve()
    frozen, review, owner = admission(args)
    require(not (root / "launch-intent.json").exists(), "Original launch intent already consumed; never replay")
    ticket = secrets.token_hex(32)
    write_new(root / "launch-intent.json", {'schema':'ck3-mod-acceptance-background-launch-intent-v1',
        'at_utc':utc(),'ticket':ticket,'run_id':frozen['run_id'],
        'steam_offline_receipt':review['receipt'],'frozen_argv':pin(root/'frozen-argv.json'),
        "admitted_lease": owner["lease"], "business_pass": False})
    argv = [sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()),
            "--run-root", str(root), "--keeper-root", str(args.keeper_root.resolve()),
            '--steam-offline-receipt',str(args.steam_offline_receipt.resolve()),
            "--supervise", "--launch-ticket", ticket]
    with (root / "host-supervisor-stdout.log").open("xb") as stdout, (root / "host-supervisor-stderr.log").open("xb") as stderr:
        child = subprocess.Popen(argv, cwd=frozen["lease_anchor"], stdout=stdout, stderr=stderr,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    write_new(root / "host-supervisor-started.json", {"at_utc": utc(), "pid": child.pid, "argv": argv,
                                                    "business_pass": False})
    deadline = time.monotonic() + 45
    start_read_error = None
    while time.monotonic() < deadline:
        if (root / "host-started.json").exists():
            try:
                host = read_json(root / "host-started.json")
            except json.JSONDecodeError as error:
                # The supervisor publishes this once-only ACK with open('x')
                # before json.dump completes. Re-read it; never start again.
                start_read_error = error
            else:
                print(json.dumps({"status": "ORIGINAL_SHARED_HOST_STARTED", "run_id": frozen["run_id"],
                    "host": host, "business_pass": False}), flush=True)
                return 0
        require(child.poll() is None, "Original host supervisor failed; inspect retained stderr and never replay")
        time.sleep(.05)
    raise TimeoutError("Original host supervisor launch not proved in budget; never replay") from start_read_error


def main(argv=None):
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
