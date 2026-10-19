"""Exact F98 maintenance: current status, fresh SEM, one public SAVE.

The retired recording is not admitted again. This local early-lazy control
keeps the ordinary Queue/Driver guards intact and never retries a tool call.
Only the sole runtime owner may install or invoke this finite source.
"""
from __future__ import annotations

import copy
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import time

MACHINE = "xenoamess-full-tower-eb9d2c1186"
BASE = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep")
T = BASE / "robert30-v20261019-campaign01/runtime"
F98 = BASE / "p51-fresh1066-v20261019-prepare01/c20-exact-clock10476-repeat98"
FROZEN_SHA = "443c6ae4f51d14235e94253f1c2d013ff58d9c299edc864c05e095b3b82bfc4f"
CLOSED_SHA = "3919da633a68a38adc8f01aebf6bdd6f3a004fa6231cfef2110849bc8f504517"
TIMING_SHA = "bd11efa68d7d5694d0b7dc3b280611a37c311e2de6aa7790bb1b110b7bf02733"
QUEUE_SHA = "ed5f8b77b5fbb69b27be204d36f28e1a2e45acd572ff7fae2658444f07f9a09d"
FREEZE_SHA = "6def1ffc381f0d532c57e54a2bc51b9bdfebef7b88a015375c0ad95eb26c9c9e"
DISPATCHER_SHA = "17f64b78241715d689f5f2a62f6ee9a169867dbd20a26d51239e45a946867269"
KIND = "c20_clock10476_status_semantic_save_maintenance"
SCHEMA = "xar.C20-clock10476-maintenance/v1"
ERROR = "Error executing tool ck3_auto_turn: exact-day native clock did not stop the map"
STATUS_STEP = "research-query-tactical-daily-sentinel-v1"
GAME, BIRTH, DATE, CYCLES = 30852, 134368995759027619, 53274624, 4753
EPISODE = "native-40526-1bec95182886"
LIVE = {GAME: BIRTH, 9808: 134369190683587530, 30936: 134369190706095204,
        53688: 134368999873257432}


def require(ok, why):
    if not ok:
        raise ValueError("F98 finite maintenance denied: " + why)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _raw(path, limit=262144):
    with Path(path).open("rb") as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, "bounded input exceeded: " + str(path))
    return raw


def _exists(path):
    return Path(path).exists()


def _pinned(ref, limit=262144):
    raw = _raw(ref["path"], limit)
    require(type(ref["bytes"]) is int and len(raw) == ref["bytes"]
            and _sha(raw) == ref["sha256"], "pinned input changed: " + ref["path"])
    return raw, json.loads(raw)


def live_birth(pid):
    """Fresh kernel read of an exact generation; an exited PID is not live."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = (wintypes.HANDLE,) + (ctypes.POINTER(wintypes.FILETIME),) * 4
    kernel.GetProcessTimes.restype = wintypes.BOOL
    kernel.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    kernel.GetExitCodeProcess.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x101000, False, pid)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        born, exited, kt, ut = (wintypes.FILETIME() for _ in range(4))
        code = wintypes.DWORD()
        if not kernel.GetProcessTimes(handle, ctypes.byref(born), ctypes.byref(exited), ctypes.byref(kt), ctypes.byref(ut)):
            raise ctypes.WinError(ctypes.get_last_error())
        require(kernel.WaitForSingleObject(handle, 0) == 258
                and kernel.GetExitCodeProcess(handle, ctypes.byref(code)) and code.value == 259,
                "owned process is no longer live: " + str(pid))
        return (born.dwHighDateTime << 32) | born.dwLowDateTime
    finally:
        kernel.CloseHandle(handle)


def transform_dispatcher_v1(raw, helper_sha):
    """Append one exact wrapper; every legacy dispatcher byte is preserved."""
    require(type(raw) is bytes and _sha(raw) == DISPATCHER_SHA, "unused dispatcher baseline differs")
    require(type(helper_sha) is str and len(helper_sha) == 64
            and all(c in "0123456789abcdef" for c in helper_sha), "helper pin required")
    suffix = ("\nrecover_before_clock10476 = recover_zero_rpc_preflight\n"
        "async def recover_zero_rpc_preflight(queue,session,request,path,env):\n"
        "    if request.get('arguments') == {'repair_kind': '" + KIND + "'}:\n"
        "        source=Path(__file__).with_name('root_c20_clock10476_maintenance.py')\n"
        "        payload=source.read_bytes()\n"
        "        if len(payload)>24576 or hashlib.sha256(payload).hexdigest()!='" + helper_sha + "':\n"
        "            raise ValueError('reviewed F98 maintenance source differs')\n"
        "        scope={'__file__':str(source)}\n"
        "        exec(compile(payload,str(source),'exec'),scope)\n"
        "        return await scope['recover'](queue,session,request,path,env)\n"
        "    return await recover_before_clock10476(queue,session,request,path,env)\n").encode()
    output = raw + suffix
    require(output[:-len(suffix)] == raw, "dispatcher prefix changed")
    return output


def _inputs(q, env):
    raw = _raw(F98 / "FROZEN.json", 16384)
    require(len(raw) == 7799 and _sha(raw) == FROZEN_SHA, "exact F98 source manifest required")
    manifest = json.loads(raw)
    require(manifest["machine_id"] == MACHINE and manifest["business_commit"]
            == "f19864de1cc073eed62617faad2307c57ad45a97", "machine/business source differs")
    values, raws = {}, {}
    for key, ref in manifest["sources"].items():
        raws[key], values[key] = _pinned(ref["frozen"])
        require(ref["original"]["sha256"] == ref["frozen"]["sha256"], "source provenance differs")
    _, clock = _pinned(manifest["readonly_current_clock"])
    for name, size, sha in (("EXISTING-CLOCK-TIMING-10476.json", 5955, TIMING_SHA),
                            ("RECORDING-CLOSED-PUBLISHER-KEPT.json", 2935, CLOSED_SHA)):
        data = _raw(F98 / name, 8192)
        require(len(data) == size and _sha(data) == sha, "closed diagnostic changed: " + name)
    closed = json.loads(_raw(F98 / "RECORDING-CLOSED-PUBLISHER-KEPT.json"))
    require(closed["machine_id"] == MACHINE and closed["status"] == "RECORDING_CLOSED_PUBLISHER_GAME_SDK_KEPT"
            and closed["publisher_STOP_submitted"] is False and closed["NEXT"] == 10477,
            "actual normal recorder closure required")
    for name in ("capture_closed", "cleanup", "completed", "STOP"):
        _pinned(closed[name])
    _, capture = _pinned(closed["capture_closed"])
    require(capture["game_pid"] == GAME and capture["game_creation_filetime"] == BIRTH
            and capture["inputs_unbound"] is True and capture["engine_close"] == {
                "requested": True, "actual_exit_code": 0, "normal_exit_proven": True, "forced_process_calls": 0}
            and closed["kernel"]["worker"]["wait0"] == 0
            and closed["kernel"]["worker"]["GetExitCodeProcess"] == 0,
            "normal capture closure/worker exit differs")
    require(Path(q.record_job).resolve() == Path(closed["capture_closed"]["path"]).parent.resolve(),
            "Queue recorder is not the closed source")
    require(_sha(_raw(T / "root_p37c20_sdk_queue.py", 1024**2)) == QUEUE_SHA
            and _sha(_raw(T / "ROOT-FINAL-SDK-FREEZE-P37C20.json", 1024**2)) == FREEZE_SHA,
            "actual Queue/source freeze changed")
    require(all(Path(env[k]).resolve() == (T / v).resolve() for k, v in (
        ("N", "."), ("Q", "p37-queue"), ("INBOX", "p37-requests"), ("OUTBOX", "p37-responses"))),
        "runtime roots differ")
    state, gov, auto = values["state"], values["gov"], values["AUTO"]
    require(q.full_loop_state == state and _raw(env["Q"] / "ROOT-CUMULATIVE-LOOP-STATE.json") == raws["state"]
            and _raw(env["Q"] / "ROOT-GOVERNANCE-RESULT-STATE.json") == raws["gov"], "old state/governance CAS differs")
    require(isinstance(q.halted, dict) and q.halted["request"] == auto["request"] and q.halted["row"] == auto
            and _raw(q.halted["response"]) == raws["AUTO"]
            and Path(q.halted["response"]).resolve() == (env["OUTBOX"] / "10476-1-result.json").resolve(),
            "original failed received AUTO differs")
    require(auto["request"]["sequence"] == 10476 and auto["request"]["tool"] == "ck3_auto_turn"
            and auto["request"]["arguments"] == {}
            and auto.get("client_error") is None and auto["result"]["is_error"] is True
            and auto["result"]["result_type"] == "complete" and auto["result"]["structured_content"] is None
            and [r.get("text") for r in auto["result"]["content"]] == [ERROR], "F98 failure shape differs")
    pending = state["pending_cycle"]
    plan = values["plan"]["result"]["structured_content"]
    require(state["completed_cycles"] == CYCLES and state["before"]["date_raw"] == DATE-24
            and state["before"]["native_revision"] == 4366 and state["before"]["revision"] == 5
            and pending["global_turn"] == 4754 and pending["auto_sequence"] == 10476
            and pending["stage"] == "auto_unsettled" and gov["pending_cycle"] == pending
            and gov["completed_cycles"] == CYCLES and gov["new_business_credit"] == 0
            and all(state.get(k) is None for k in ("pending_checkpoint", "terminal", "pending_natural_succession", "pending_unsafe_route_halt"))
            and plan["snapshot_id"] == "native:4366" and plan["revision"] == 5
            and values["plan"]["request"]["parent_sequence"] == 10476,
            "exact unknown failed frontier required")
    require(clock["machine_id"] == MACHINE and clock["clock"]["date_raw"] == DATE
            and clock["clock"]["paused"] is True and clock["clock"]["played_character_id"] == 40526
            and clock["kernel_before"] == clock["kernel_after"] and clock["kernel_before"]["pid"] == GAME
            and int(clock["kernel_before"]["creation_filetime"]) == BIRTH and clock["kernel_before"]["wait0"] == 258,
            "late readonly clock identity differs")
    require(q.next_sequence == values["NEXT"]["next_sequence"] == 10477
            and _raw(T / "NEXT-SEQUENCE-P37.json") == raws["NEXT"]
            and q.launch["pid"] == GAME and q.job["game_creation_filetime"] == BIRTH
            and q.governance_result_state == gov["state"] and q.lifestyle_pending_focus == gov["pending_focus"]
            and q.result_classifier_pin == gov["classifier"], "source/current generation/business cache differs")
    method = q.recover_partial_life_advance
    ns = getattr(method, "__func__", method).__globals__
    require(Path(ns["__file__"]).resolve() == (T / "root_p37c20_sdk_queue.py").resolve(), "actual inherited namespace required")
    return state, gov, raws, ns


def _fresh(body, q, state, ns):
    frame = ns["frame"](body, semantic=True, expected_lifecycle=q.expected_lifecycle_binding)
    diag = body.get("diagnostics") or {}
    hello = diag.get("hello") or {}
    require(body.get("one_life_terminal") is False and body.get("one_life_terminal_reason") is None
            and frame["actor_character_id"] == 40526 and frame["episode_run_id"] == EPISODE
            and frame["date_raw"] == DATE and type(frame["native_revision"]) is int
            and frame["native_revision"] > 4366 and frame["revision"] > 5
            and frame["snapshot_id"] == f"native:{frame['native_revision']}"
            and diag.get("bridge_pid") == hello.get("pid") == GAME
            and diag.get("connection_generation") == hello.get("connection_generation") == 4
            and diag.get("pipe_name") == q.launch["pipe"] and hello.get("ck3_build_match") is True
            and hello.get("game_adapter_status") == "ready" and hello.get("game_adapter_id") == "ck3-1.20.0.4-msvc-x64"
            and body.get("campaign_goal") == state["campaign_goal_anchor"], "fresh paused Native/identity/goal/date differs")
    return frame


async def recover(q, session, request, path, env, *, birth_reader=live_birth):
    require(request.get("command") == "clear_zero_rpc_preflight_rejection" and "tool" not in request
            and request.get("arguments") == {"repair_kind": KIND} and request.get("sequence") == 10477
            and path.name == "10477-1-result.json", "one exact unused early maintenance control required")
    old, gov, raws, ns = _inputs(q, env)
    audit_path = env["Q"] / "EXACT-CLOCK10476-MAINTENANCE-10477.json"
    started_path = audit_path.with_name(audit_path.stem + "-STARTED.json")
    save_event = env["Q"] / "CUMULATIVE-SAVE-004753.json"
    require(not any(_exists(p) for p in (audit_path, started_path, save_event, env["OUTBOX"] / path.name))
            and not any(_exists(env[root] / f"{seq}-1-result.json") for root in ("INBOX", "OUTBOX") for seq in (10478,10479,10480))
            and not any(_exists(env["Q"] / f"INFLIGHT-{seq}.json") for seq in (10477,10478,10479,10480)),
            "maintenance is create-only; tools are never replayed")

    def guard():
        # The exact original guard's non-record prefix, never the active-record
        # terminal/output/growth subsection. Ordinary guard is untouched.
        require(not any(_exists(p) for p in (T / "REQUEST-ADMISSION-CLOSED-C20", T / "EXIT-SDK-P37C20", env["Q"] / "EXIT-SDK-P37C20")), "SDK admission explicitly ended")
        admission = env["read"](T / "STORAGE-ADMISSION.json")
        require(admission.get("status") == "ADMITTED" and admission["review_at_utc"] == q.admission["review_at_utc"], "storage admission changed")
        require(env["shutil"].disk_usage(T).free > admission["disk_reserve_bytes"], "admitted disk headroom insufficient")
        require(q.artifact_bytes() + env["REPLY_RESERVE"] <= q.args.artifact_cap_bytes, "queue artifact allocation exhausted")
        require(all(birth_reader(pid) == birth for pid, birth in LIVE.items()), "same live Game/SDK/publisher generation required")

    def consume(child):
        sequence = child.get("sequence")
        require(type(sequence) is int and sequence == q.next_sequence, "one current unused sequence required")
        guard()
        q.next_sequence += 1
        env["atomic"](T / "NEXT-SEQUENCE-P37.json", {"next_sequence":q.next_sequence,"at_utc":env["now"]().isoformat()}, replace=True, limit=16384)
        return sequence

    guard()
    consume(request)
    q.held_control = path.name
    audit = {"schema":SCHEMA,"machine_id":MACHINE,"utc":env["now"]().isoformat(),"request":request,
             "source_manifest_sha256":FROZEN_SHA,"closed_record_sha256":CLOSED_SHA,
             "original_pending_cycle":copy.deepcopy(old["pending_cycle"]),"failed_cycle_credit":0,"failed_day_credit":0,
             "original_AUTO_replayed":False,"original_Arm_generation":"unknown","sentinel_stop_claimed":False,
             "new_pause_arm_resume_cancel":0,"ordinary_recording_admitted":False,"native_maintenance":True,
             "fixed_tools":["ck3_execute_step",env["SEMANTIC"],"ck3_save_checkpoint"],"calls":[],
             "record_only_guard_omitted":"closed recorder terminal/output/growth only; ordinary guard unchanged"}
    env["atomic"](started_path,audit,limit=8192)
    env["atomic"](env["Q"] / "INFLIGHT-10477.json",{"request":request,"native_maintenance":True,"replay_allowed":False},limit=16384)
    original_halt, original_attempt = q.halted, q.current_attempt
    reanchored = False
    row_bytes = 0

    async def once(tool, arguments, sequence):
        nonlocal row_bytes
        guard()
        child_path = env["OUTBOX"] / f"{sequence}-1-result.json"
        child = {"sequence":sequence,"tool":tool,"arguments":arguments,"source":"F98 fixed maintenance; no AUTO replay"}
        require(not _exists(child_path), "tool already has an original response")
        env["atomic"](env["INBOX"] / child_path.name,child,limit=4096)
        consume(child)
        context={"request":child,"replay_allowed":False,"native_maintenance":True}
        env["atomic"](T / "CURRENT-REQUEST-P37.json",{**child,"at_utc":env["now"]().isoformat()},replace=True,limit=16384)
        env["atomic"](env["Q"] / f"INFLIGHT-{sequence}.json",context,limit=16384)
        at, mono = env["now"]().isoformat(), time.monotonic()
        try:
            result=await session.call_tool(tool,arguments,read_timeout_seconds=q.call_budget(tool))
            row={"started_at_utc":at,"ended_at_utc":env["now"]().isoformat(),"elapsed_seconds":time.monotonic()-mono,
                 "request":child,"result":result.model_dump(mode="json")}
        except Exception as error:
            row={"started_at_utc":at,"ended_at_utc":env["now"]().isoformat(),"elapsed_seconds":time.monotonic()-mono,
                 "request":child,"client_error":repr(error),"replay_allowed":False}
        size=len(json.dumps(row,ensure_ascii=False,separators=(",",":")).encode())
        limit=32768 if sequence==10480 else 196608-row_bytes
        require(size<=limit,"bounded original response too large; no resend")
        env["atomic"](child_path,row,limit=min(limit,env["REPLY_RESERVE"]))
        if sequence!=10480: row_bytes+=size
        audit["calls"].append({"sequence":sequence,"tool":tool,"path":str(child_path),"sha256":_sha(_raw(child_path))})
        guard()
        return row, child_path

    def persist_checked(work):
        q.full_loop_state=work
        q.persist_loop_state()
        require(json.loads(_raw(env["Q"] / "ROOT-CUMULATIVE-LOOP-STATE.json"))==work
                and json.loads(_raw(env["Q"] / "ROOT-GOVERNANCE-RESULT-STATE.json"))=={**gov,"pending_cycle":None},
                "two-file metadata readback differs; no transaction claim")

    try:
        status_row,_=await once("ck3_execute_step",{"step":STATUS_STEP},10478)
        try:
            status=env["decoded"](status_row)
            slot=status.get("tactical_daily_sentinel")
            audit["current_slot_observed"]=status.get("step")==STATUS_STEP and status.get("accepted") is True and isinstance(slot,dict)
            audit["current_slot_readback"]=copy.deepcopy(slot) if audit["current_slot_observed"] else None
        except Exception as error:
            audit.update(current_slot_observed=False,current_slot_readback=None,status_unavailable=str(error))
        row,semantic_path=await once(env["SEMANTIC"],{},10479)
        body=env["decoded"](row)
        fresh=_fresh(body,q,old,ns)
        require(_raw(env["Q"] / "ROOT-CUMULATIVE-LOOP-STATE.json")==raws["state"]
                and _raw(env["Q"] / "ROOT-GOVERNANCE-RESULT-STATE.json")==raws["gov"]
                and q.full_loop_state==old,"pre-reanchor state CAS changed")
        work=copy.deepcopy(old)
        work.update(before=fresh,before_metrics_response=str(semantic_path),pending_cycle=None,
                    checkpoint_dirty_since_save=True,before_source_kind="actual_F98_maintenance_semantic_reanchor",
                    exact_clock10476_recovery_last={"audit":str(audit_path),"failed_cycle_credit":0,
                        "original_AUTO_replayed":False,"sentinel_stop_claimed":False})
        audit.update(status="FRESH_REANCHOR_COMMIT_REQUIRED",fresh_frame=fresh,counts_unchanged=True)
        env["atomic"](audit_path,audit,limit=16384)
        persist_checked(work)
        reanchored=True
        q.semantic=body  # complete fresh event/modal/war/army payload retained
        audit["status"]="FRESH_REANCHORED_SAVE_NOT_YET_SUBMITTED"
        env["atomic"](audit_path,audit,replace=True,limit=16384)
        row,save_path=await once("ck3_save_checkpoint",{"expected_revision":fresh["revision"]},10480)
        saved=env["decoded"](row)
        checkpoint=saved.get("checkpoint")
        require(saved.get("step")=="save-checkpoint" and saved.get("accepted") is True
                and isinstance(checkpoint,dict) and checkpoint.get("status")=="saved"
                and checkpoint.get("date_raw")==DATE and checkpoint.get("episode_character_id")==40526
                and checkpoint.get("episode_run_id")==EPISODE
                and checkpoint.get("succession_lifecycle")==old["actual_saved_checkpoint"]["succession_lifecycle"],
                "public SAVE outcome unknown/mismatched; never resend")
        q.check_after("ck3_save_checkpoint",{"expected_revision":fresh["revision"]},saved)
        # Original canonical cadence and checkpoint finisher; no AUTO classifier.
        work["pending_checkpoint"]={"global_turn":CYCLES,"semantic_response":str(semantic_path)}
        q.finish_cumulative_checkpoint(saved,save_path)
        expected_counts={**old["counts"],"checkpoint_saved":old["counts"]["checkpoint_saved"]+1}
        require(work["completed_cycles"]==CYCLES and work["counts"]==expected_counts
                and work["pending_cycle"] is None and work["pending_checkpoint"] is None
                and work["actual_saved_checkpoint"]==checkpoint and work["checkpoint_dirty_since_save"] is False,
                "saved bookkeeping differs from original checkpoint-only semantics")
        persist_checked(work)
        guard()
        audit.update(status="MAINTENANCE_SAVED_SDK_MAINTENANCE_REQUIRED",saved_checkpoint=checkpoint,
                     completed_cycles_before_after=CYCLES,checkpoint_saved_count_before=73,checkpoint_saved_count_after=74,
                     ordinary_FULL_permitted=False,new_MCP_calls=3,metadata_files_are_atomic_transaction=False)
        env["atomic"](audit_path,audit,replace=True,limit=16384)
        env["atomic"](env["OUTBOX"] / path.name,{"request":request,"result":{"is_error":False,"structured_content":audit}},limit=16384)
        q.halted=q.current_attempt=q.held_control=None
        return True
    except Exception as error:
        # A committed fresh anchor/SAVE must never be rolled back in RAM to the
        # old timeline. Disk may be partly written; preserve that honest state.
        if not reanchored and not _exists(audit_path):
            q.full_loop_state=old
        q.halted,q.current_attempt,q.held_control=original_halt,original_attempt,None
        audit.update(status="F98_MAINTENANCE_FAILED_HALT_RETAINED",message=str(error),
                     reanchor_committed=reanchored,metadata_may_be_partly_committed=_exists(audit_path),
                     retry_allowed=False,new_MCP_calls=len(audit["calls"]))
        env["atomic"](audit_path,audit,replace=_exists(audit_path),limit=16384)
        env["atomic"](env["OUTBOX"] / path.name,{"request":request,"result":{"is_error":True,"structured_content":audit}},limit=16384)
        return True
