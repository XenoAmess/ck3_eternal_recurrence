"""Default-OFF, Root-reviewed owned suspended Python probe. No resume/injection."""
from pathlib import Path
import hashlib
import inspect
import json
import os
import secrets
import sys
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "_runtime/m7-prenative-owned-attempt01"
for part in (REPO, REPO / "tools", REPO / "ck3_autonomous_player/src"):
    sys.path.insert(0, str(part))


def fingerprint(value):
    path = Path(inspect.getfile(value)).resolve()
    return {"path": path.relative_to(REPO).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def require(ok, reason):
    if not ok:
        raise ValueError("owned qualification denied: " + reason)


def run():
    from xar_autoplayer import runtime
    from xar_autoplayer.bridge import native_loaded_provider_custody_v1 as custody
    from xar_autoplayer.bridge import native_loaded_provider_windows_v1 as windows
    from g2_saved_campaign import canonical_native_provider_chain_v1 as chain
    from g2_saved_campaign.owned_python_launch_v1 import owned_python_launch_v1
    from ck3_live_run_id import current_machine_id
    machine = current_machine_id()
    if os.name != "nt" or machine != "xenoamess-full-tower-eb9d2c1186":
        raise ValueError("exact owned Windows machine required")
    if ROOT.exists():
        raise FileExistsError(ROOT)
    executable, env = owned_python_launch_v1()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    ROOT.mkdir()
    lease = ROOT / "owned-lease.bin"
    data = b"owned preload lease; no DLL\n"
    with lease.open("xb") as stream:
        stream.write(data)
    facade = windows.WindowsNativeCustodyFacadeV1(enabled=True)
    factory = target = job = None
    result = {"machine_id": machine, "observed_at_utc": datetime.now(timezone.utc).isoformat(),
              "status": "FAILED_OR_UNKNOWN", "resume_calls": 0, "inject_calls": 0,
              "Native_Game_H": "NOTRUN", "source_root": str(REPO)}
    success = False
    try:
        command = [executable, "-B", "-c", "raise SystemExit('must remain suspended')"]
        job = runtime._create_kill_on_close_job("XarAutoplayer-Crash-" + secrets.token_hex(16))
        target = runtime._create_suspended_process(command, ROOT, env, start_minimized=True)
        result["target_pid"] = target.pid
        runtime._assign_process_to_job(job, target)
        result["sources"] = [fingerprint(v) for v in (runtime._apply_pre_native_resume_v1,
            chain.CanonicalPreloadFactoryV1, windows.WindowsNativeCustodyFacadeV1,
            custody.prepare_canonical_cold_custody_v1)]
        config = runtime.NativeBridgeLaunchConfig("native-headless", r"\\.\pipe\xar_owned_preload_" + secrets.token_hex(16), lease, lease)
        factory = chain.CanonicalPreloadFactoryV1(facade=facade, machine_id=machine,
            expected_dll_sha256=hashlib.sha256(data).hexdigest(),
            entry_source_pins=((str(Path(__file__).resolve()), hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),), enabled=True)
        holder = runtime._apply_pre_native_resume_v1(target, config, factory.pre_native_resume)
        require(type(holder) is custody._PreloadCustodyV1 and holder.target is target, "same typed holder")
        require(target.resumed is False and target.poll() is None and factory.origin is not None, "original suspended target")
        require(target._native_preload_custody_v1 is holder, "original runtime hook retained holder")
        result["target_identity"] = {**vars(holder.process), "creation_filetime": str(holder.process.creation_filetime)}
        phase = facade._preload_mapping_phase_v1
        result["preload_phase"] = {k: phase[k] for k in ("stage", "status", "images", "last_walk_regions")}
        close = factory.close()
        require(holder.closed and not holder._owned and close.issued is False, "holder revoked and own handles released")
        borrowed = facade.observe_process(target._process_handle)
        require(custody._same_process(holder.process, borrowed) and target.poll() is None
                and target.resumed is False, "borrowed exact target remains alive after holder close")
        result["borrowed_target_still_alive_after_holder_close"] = True
        result["borrowed_full_birth_after_close"] = str(borrowed.creation_filetime)
        success = True
    except Exception as error:
        result["error"] = type(error).__name__ + ":" + str(error)[:240]
    finally:
        failures = []
        def clean(label, call):
            try:
                return call()
            except Exception as error:
                failures.append(label + ":" + type(error).__name__)
        if factory is not None:
            clean("holder", factory.close)
        if target is not None:
            result["resumed_final"] = target.resumed
            clean("terminate_exact", target.terminate_exact)
            result["owned_child_controlled_exit"] = clean("wait", lambda: target.wait(10))
        if job is not None:
            result["job_active_after"] = clean("Job_query", lambda: runtime._job_active_processes(job))
            if result["job_active_after"] != 0:
                clean("Job_terminate", lambda: runtime._terminate_job(job))
                result["job_active_after_cleanup"] = clean("Job_requery", lambda: runtime._job_active_processes(job))
                success = False
            clean("Job_close", lambda: runtime._close_job(job))
        if target is not None:
            clean("target_close", target.close)
        result["facade_cleanup"] = clean("facade", facade.close_all_owned)
        clean("lease", lease.unlink)
        if failures:
            result["cleanup_errors"] = failures
    success = success and not failures and result.get("owned_child_controlled_exit") == 1 \
        and result.get("job_active_after") == 0 \
        and result.get("facade_cleanup", {}).get("owned_handles_remaining") == 0
    result["status"] = "OWNED_PRE_RESUME_PASS" if success else "FAILED_OR_UNKNOWN"
    raw = (json.dumps(result, sort_keys=True) + "\n").encode()
    if len(raw) > 2048:
        raise ValueError("owned receipt exceeds joint temporary cap")
    with (ROOT / "RECEIPT.json").open("xb") as stream:
        stream.write(raw)
    print(json.dumps(result))
    if not success:
        raise SystemExit(1)


if __name__ == "__main__":
    if sys.argv[1:] == ["--execute-owned-preresume"]:
        run()
    elif not sys.argv[1:]:
        print('{"status":"DISABLED","process_created":false}')
    else:
        raise SystemExit("explicit Root-owned-probe release required")
