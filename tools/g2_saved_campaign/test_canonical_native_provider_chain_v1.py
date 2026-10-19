"""Default-OFF source contracts and opt-in four-child kernel qualification.

Kernel resources/creation/lease/peers are real. Native module/hello observations
are explicitly synthetic; this never qualifies CK3, a loaded DLL, or actual H.
"""
import ast
import ctypes
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest

REPO=Path(__file__).resolve().parents[2]
for part in (REPO,REPO/"tools",REPO/"ck3_autonomous_player/src"):
    if str(part) not in sys.path:sys.path.insert(0,str(part))

from xar_autoplayer import runtime
from xar_autoplayer.bridge import native_loaded_provider_custody_v1 as custody
from xar_autoplayer.bridge import native_loaded_provider_origin_v1 as origin
from xar_autoplayer.bridge import native_loaded_provider_windows_v1 as windows
from xar_autoplayer.bridge.native_loaded_provider_origin_io_v1 import OriginKernelIOV1
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver,NativeNamedPipeServer,NativeProtocolState
from xar_autoplayer.bridge.successor_ui_app_owner_v1 import SuccessorUIAppOwner
from tools.g2_saved_campaign import canonical_native_provider_chain_v1 as chain
from tools.g2_saved_campaign.owned_python_launch_v1 import owned_python_launch_v1

MACHINE="xenoamess-full-tower-eb9d2c1186"
DATA=b"owned canonical source chain; not a Native DLL\n"
RUNS=[]


class SyntheticNativeReads:
    """Delegate all kernel/file/peer calls; synthetic module boundary only."""
    def __init__(self):
        self.real=windows._Win32ReadsV1();self.native_dos=self.native_nt=None;self.module_calls=0
    def __getattr__(self,name):return getattr(self.real,name)
    def modules(self,handle):
        self.module_calls+=1
        return ((0x7FF100000000,4096,self.native_dos),) if self.native_dos else ()
    def mapped_file_name(self,handle,base):return self.native_nt


def actual_shape_owner(holder,endpoint):
    driver=object.__new__(NativeHeadlessGameplayDriver)
    driver.endpoint,driver.pipe_name,driver._session_bridge_pid=endpoint,holder.pipe_name,holder.process.pid
    driver.state=NativeProtocolState(holder.pipe_name)
    driver.state.ingest({"type":"hello","protocol_version":1,"pid":holder.process.pid,
                        "capabilities":[],"connection_generation":1})
    owner=object.__new__(SuccessorUIAppOwner)
    owner.driver,owner.machine,owner.epoch,owner.lock=driver,MACHINE,origin._epoch(),threading.RLock()
    owner.service=SimpleNamespace(driver=driver,_successor_ui_app_owner_v1=owner)
    driver._player_heir_candidate_owner_v1=owner
    owner._player_heir_loaded_provider_v1=None
    owner._player_heir_loaded_custody_v1=None
    owner._player_heir_game_identity_cache_v1=None
    return owner


class CanonicalSourceContracts(unittest.TestCase):
    def test_default_off_has_no_IO_and_no_creator(self):
        factory=chain.CanonicalPreloadFactoryV1(facade=object(),machine_id=MACHINE,
            expected_dll_sha256="a"*64)
        self.assertIsNone(factory.pre_native_resume(None,None))
        self.assertIsNone(chain.prepare_child_v1(None,role="owner",command=[],env={},cwd="."))
        self.assertIsNone(chain.receive_child_bootstrap_v1({},facade=object()))
        self.assertIsNone(origin.prepare_canonical_origin_v1(custody=None))
        self.assertIsNone(runtime._apply_pre_native_resume_v1(None,None,None))
        self.assertEqual(chain.consume_private_bootstrap_args_v1(["entry","--xar-private-preload","{}"]),
                         (["entry","--xar-private-preload","{}"],None))

    def test_private_locations_are_consumed_before_original_cli_without_granting_source(self):
        argv=["entry","--original","--xar-private-preload",'{"locations":{}}']
        self.assertEqual(chain.consume_private_bootstrap_args_v1(argv,enabled=True),
                         (["entry","--original"],{"locations":{}}))
        self.assertEqual(argv[2],"--xar-private-preload")
        for suffix in (["--xar-private-preload","{}","foreign"],
                       ["--xar-private-preload","{}","--xar-private-preload","{}"]):
            with self.subTest(suffix=suffix),self.assertRaises(ValueError):
                chain.consume_private_bootstrap_args_v1(["entry",*suffix],enabled=True)

    def test_boolean_or_JSON_cannot_promote_received_source(self):
        value=object.__new__(custody._PreloadCustodyV1)
        value.seal,value.source_role,value._preload_source_verified=custody._RESOURCE_SEAL,"received",True
        value._origin_session_v1={"source_verified":True}
        with self.assertRaisesRegex(ValueError,"continuity is not qualified"):
            origin.require_original_preload_origin_v1(value,object())
        with self.assertRaisesRegex(ValueError,"original typed custody"):
            origin.require_original_preload_origin_v1({"source_verified":True},object())

    def test_epoch_mismatch_fails_before_transport_or_issuer(self):
        session=object.__new__(origin._OriginSessionV1)
        holder=SimpleNamespace(closed=False);owner=SimpleNamespace(
            _player_heir_loaded_custody_v1=holder,epoch="wrong")
        holder.owner=owner;session.holder,session.epoch,session.lock=holder,"actual",threading.RLock()
        with self.assertRaisesRegex(ValueError,"owner/epoch"):
            session.require(owner,full=True)

    def test_private_readback_rejects_replay_or_different_original_resources(self):
        birth=134368602545256921
        game=custody._ProcessReadbackV1(71,birth,"2026-10-19T05:10:54.5256921Z",r"C:\own\python.exe",True)
        original=custody._ProcessReadbackV1(72,birth,game.creation_date,game.executable,True)
        app=custody._ProcessReadbackV1(73,birth,game.creation_date,game.executable,True)
        file=custody._DLLReadbackV1(r"C:\own\lease.bin",1,b"i"*16,"a"*64,3)
        for mutate in ("none","sequence","nonce","file","epoch","peer","root"):
            with self.subTest(mutate=mutate):
                holder=object.__new__(custody._PreloadCustodyV1)
                holder.closed,holder.process_handle,holder.process,holder.dll=False,101,game,file
                holder._creator_source_digest_v1="b"*64
                record=SimpleNamespace(active=True,parent_handle=102,revoke_handle=103)
                peer=99 if mutate=="peer" else original.pid
                api=SimpleNamespace(wait_zero=lambda h:0 if mutate=="root" and h==103 else 0x102,
                                    private_parent_pid=lambda h:peer)
                facade=SimpleNamespace(_received_preloads_v1={holder:record})
                holder.facade=facade
                owner=SimpleNamespace(_player_heir_loaded_custody_v1=holder,epoch="actual")
                holder.owner=owner
                state={"requests":[]}
                def send(handle,value):state["requests"].append(value)
                def recv(handle):
                    request=state["requests"][-1]
                    body={"epoch":"actual","creator":"b"*64,"target":origin._process_key(game),
                        "file":origin._file_key(file),"origin":origin._process_key(original),"app":origin._process_key(app)}
                    response={"kind":"original_preload_live","sequence":request["sequence"],"nonce":request["nonce"],"body":body}
                    if mutate=="sequence":response["sequence"]-=1
                    if mutate=="nonce":response["nonce"]="stale"
                    if mutate=="file":body["file"][3]="c"*64
                    if mutate=="epoch":body["epoch"]="other"
                    return response
                session=object.__new__(origin._OriginSessionV1)
                session.holder,session.origin_handle,session.origin,session.app=holder,104,original,app
                session.epoch,session.sequence,session.lock,session.handle="actual",0,threading.RLock(),105
                session.io=SimpleNamespace(api=api,send=send,recv=recv)
                if mutate=="none":
                    session.require(owner,full=True);session.require(owner,full=False)
                    self.assertEqual([v["sequence"] for v in state["requests"]],[1,2])
                else:
                    with self.assertRaises(ValueError):session.require(owner,full=True)
                    if mutate in ("peer","root"):self.assertEqual(state["requests"],[])

    def test_upward_unknown_rights_does_not_open_a_pid_or_register_a_handle(self):
        io=object.__new__(OriginKernelIOV1);calls=[]
        def duplicate(*args):calls.append(args);return False
        def require(ok,why):
            if not ok:raise PermissionError("actual child handle duplicate unavailable")
        io.api=SimpleNamespace(duplicate=duplicate,current=lambda:-1,PROCESS_READ_ACCESS=0x100410,_ok=require)
        io.facade=SimpleNamespace(_owned={})
        with self.assertRaises(PermissionError):io.pull_read_process(901,902,holder=object())
        self.assertEqual(len(calls),1);self.assertEqual(io.facade._owned,{})

    def test_missing_actual_chain_cannot_bind_even_if_claim_has_expected_roles(self):
        original=object.__new__(origin._CanonicalOriginV1)
        with self.assertRaisesRegex(ValueError,"actual owner edge"):
            original.bind_actual_chain({"roles":["owner","Queue","MCPApp"],"source_verified":True})

    def test_missing_or_wrong_entry_source_pin_refuses_before_preload_IO(self):
        path=str(Path(__file__).resolve())
        digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
        self.assertEqual(chain._verified_entry_sources(((path,digest),)),((path,digest),))
        for pins in ((),((path,"0"*64),),((path,digest),(path,digest))):
            with self.subTest(pins_count=len(pins)),self.assertRaises(ValueError):
                factory=chain.CanonicalPreloadFactoryV1(facade=object(),machine_id=MACHINE,
                    expected_dll_sha256="a"*64,entry_source_pins=pins,enabled=True)
                factory.pre_native_resume(None,None)

    def test_only_the_actual_direct_script_operand_can_bind_frozen_source(self):
        entry=str(Path(__file__).resolve());python=str(Path(sys.executable).resolve())
        for flags in ([],["-B"],["-u"],["-X","utf8"],["-B","-X","utf8","-u"]):
            with self.subTest(flags=flags):
                command=[python,*flags,entry,"--owned-canonical-role"]
                self.assertEqual(chain._require_direct_entry_command_v1(command,entry),1+len(flags))
        bad=(
            [python,"-c","cooperating_bootstrap()",entry],
            [python,"-m","cooperating_module",entry],
            [python,"--",entry],
            [python,"-I",entry],
            [python,"-X","dev",entry],
            [python,"-X","utf8"],
            [python,"-B","-B",entry],
            [python,str(Path(chain.__file__).resolve()),entry],
            [python,"-",entry],
        )
        for command in bad:
            with self.subTest(command=command[1:]),self.assertRaises(ValueError):
                chain._require_direct_entry_command_v1(command,entry)
        # After the script operand these are script arguments, not Python modes.
        self.assertEqual(chain._require_direct_entry_command_v1([python,entry,"-c","arg"],entry),1)

    def test_returned_image_uses_retained_creator_path_rules_before_child_ACK(self):
        actual=custody._ProcessReadbackV1(71,134368602545256921,
            "2026-10-19T05:10:54.5256921Z",r"C:\own\python.exe",True)
        chain._require_returned_image_v1(actual,r"C:\OWN\python.exe")
        plan=object.__new__(chain._ChildPlanV1)
        plan.command=(r"C:\different\python.exe",)
        plan.io=SimpleNamespace(facade=SimpleNamespace(observe_process=lambda handle:actual))
        # No connected()/send()/ACK methods exist: image refusal must occur first.
        with self.assertRaisesRegex(ValueError,"returned child executable"):
            plan.acknowledge(SimpleNamespace(pid=71),101)

    def test_runtime_hook_is_between_actual_creation_and_both_resume_branches(self):
        tree=ast.parse(Path(runtime.__file__).read_text(encoding="utf-8"))
        launch=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="launch")
        calls={name:[] for name in ("_create_suspended_process","_apply_pre_native_resume_v1",
                                  "_resume_then_inject_after_saved_load","_resume_with_native_bridge")}
        for node in ast.walk(launch):
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in calls:
                calls[node.func.id].append(node.lineno)
        self.assertTrue(all(len(v)==1 for v in calls.values()))
        self.assertLess(calls["_create_suspended_process"][0],calls["_apply_pre_native_resume_v1"][0])
        self.assertLess(calls["_apply_pre_native_resume_v1"][0],calls["_resume_then_inject_after_saved_load"][0])
        self.assertLess(calls["_apply_pre_native_resume_v1"][0],calls["_resume_with_native_bridge"][0])

    @unittest.skipUnless(os.name=="nt","Windows original resource fixtures")
    def test_driver_disconnect_clears_before_owned_release(self):
        from ck3_autonomous_player.tests.unit.test_native_loaded_provider_custody_v1 import context,prepare
        facade,target,owner,driver,endpoint=context()
        holder=prepare(facade,target);holder.owner=owner;facade.owner=owner
        owner._player_heir_loaded_custody_v1=holder
        owner._player_heir_loaded_provider_v1=object()
        owner._player_heir_game_identity_cache_v1=object()
        driver._mark_bridge_disconnected_v1()
        self.assertIsNone(owner._player_heir_loaded_provider_v1)
        self.assertIsNone(owner._player_heir_game_identity_cache_v1)
        self.assertEqual(set(facade.closed),{facade.target,facade.dll})
        self.assertNotIn(facade.original,facade.closed)


def _actor_program():
    return [str(Path(__file__).resolve()),"--owned-canonical-role"]


def _assert_command(value,expected):
    if value!={"command":expected}:raise AssertionError("private owned fixture command differs: "+str(value))


def _run_owned_actor(hints):
    assert os.environ.get("XAR_CANONICAL_OWNED_CHAIN")=="1"
    facade=windows.WindowsNativeCustodyFacadeV1(enabled=True,_api=SyntheticNativeReads())
    result=None;plan=None
    try:
        result,io,control=chain.receive_child_bootstrap_v1(hints,facade=facade,enabled=True)
        holder=result.holder;role=hints["role"]
        executable,env=owned_python_launch_v1()
        if role=="owner":
            plan=chain.prepare_child_v1(holder,role="Queue",command=[executable,"-B","-X","utf8",*_actor_program()],
                env=env,cwd=REPO,entry_source=__file__,enabled=True)
            edge=chain.spawn_owned_popen_v1(plan,stdout=subprocess.DEVNULL,stderr=sys.stderr)
            chain.export_actual_child_chain_v1(result,io,control,edge)
            issued=io.recv(edge.control);io.send(control,issued)
            _assert_command(io.recv(control),"probe_revocation")
            io.send(edge.control,{"command":"probe_revocation"})
            report=io.recv(edge.control);io.send(control,report)
            _assert_command(io.recv(control),"report_ack")
            io.send(edge.control,{"command":"report_ack"})
            assert plan.child.wait(timeout=10)==0
            plan.child._handle.Close()
        elif role=="Queue":
            import anyio
            import mcp.os.win32.utilities as stock_windows
            async def run():
                nonlocal plan
                plan=chain.prepare_child_v1(holder,role="MCPApp",command=[executable,"-B","-X","utf8",*_actor_program()],
                    env=env,cwd=REPO,entry_source=__file__,enabled=True)
                assert len(stock_windows._process_jobs)==0
                async with chain.spawn_owned_mcp_v1(plan,errlog=sys.stderr) as (edge,streams,generation):
                    chain.export_actual_child_chain_v1(result,io,control,edge)
                    read,_write=streams
                    with anyio.fail_after(15):ready=await read.receive()
                    assert ready.message.method=="source_contract_issued"
                    issued=ready.message.params
                    assert issued["pid"]==generation.pid
                    job=stock_windows._process_jobs[plan.child]
                    exact_job=bool(stock_windows.win32job.IsProcessInJob(int(generation._handle),job))
                    assert exact_job
                    io.send(control,{"kind":"software_issued","report":issued,"real_stock_Job_member":exact_job})
                    _assert_command(io.recv(control),"probe_revocation")
                    io.send(edge.control,{"command":"probe_revocation"})
                    with anyio.fail_after(15):finished=await read.receive()
                    assert finished.message.method=="source_contract_revoked"
                    report=finished.message.params
                    assert report["pid"]==generation.pid
                    assert await plan.child.wait()==0
                    job_value=int(job)
                assert len(stock_windows._process_jobs)==0
                assert generation._closed
                flags=ctypes.c_ulong();k=facade._api.real.k
                query=k.GetHandleInformation;query.argtypes,query.restype=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ulong)],ctypes.c_int
                ctypes.set_last_error(0);assert not query(job_value,ctypes.byref(flags));assert ctypes.get_last_error()==6
                report.update(original_stock_Job_entry_removed=True,original_stock_Job_handle_closed_error=6,
                    retained_MCP_handle_closed=True,App_exit_code=0)
                io.send(control,{"kind":"chain_finished","report":report})
                _assert_command(io.recv(control),"report_ack")
            anyio.run(run)
        else:
            chain.export_actual_child_chain_v1(result,io,control)
            native_server,_=io.server(name=holder.pipe_name)
            io.connected(native_server)
            assert io.recv(native_server)=={"owned_target_pid":holder.process.pid}
            endpoint=object.__new__(NativeNamedPipeServer)
            endpoint._handle,endpoint._handle_lock,endpoint.pipe_name=native_server,threading.Lock(),holder.pipe_name
            owner=actual_shape_owner(holder,endpoint)
            facade._api.native_dos=holder.dll.final_path
            facade._api.native_nt=facade._files[holder.dll_handle].nt_path
            chain.install_received_provider_bootstrap_v1(owner.service,result,enabled=True)
            issued=origin.ensure_received_provider_v1(owner)
            assert issued.issued,issued
            provider=owner._player_heir_loaded_provider_v1
            assert holder._preload_source_verified is False
            assert provider.game_creation_filetime==holder.process.creation_filetime
            assert origin.ensure_received_provider_v1(owner) is None
            assert owner._player_heir_loaded_provider_v1 is provider
            assert facade._api.module_calls==2  # original complete-roster bookends; no second mint
            live=origin.exact_live_provider_game_v1(owner,provider)
            assert live["creation_date"]==holder.process.creation_date
            report={"pid":os.getpid(),"target_pid":holder.process.pid,"target_birth_filetime":str(provider.game_creation_filetime),
                "target_birth_ISO7":provider.game_birth,"source_verified_flag":holder._preload_source_verified,
                "unique_existing_DTO":type(provider).__name__,"Native_module_hello_boundary":"synthetic",
                "actual_H_credit":0,"SDK_source_epoch":owner.epoch,"creator_source_digest":holder._creator_source_digest_v1}
            print(json.dumps({"jsonrpc":"2.0","method":"source_contract_issued","params":report}),flush=True)
            _assert_command(io.recv(control),"probe_revocation")
            close=facade._api.real.close_handle;cleared=[]
            def check_clear(handle):
                assert owner._player_heir_loaded_provider_v1 is None
                assert owner._player_heir_game_identity_cache_v1 is None
                cleared.append(handle);return close(handle)
            facade._api.real.close_handle=check_clear
            try:origin.exact_live_provider_game_v1(owner,provider)
            except Exception:pass
            else:raise AssertionError("revoked root still qualified")
            assert holder.closed and owner._player_heir_loaded_provider_v1 is None
            assert not holder._owned and owner._player_heir_loaded_custody_v1 is None
            io.send(native_server,{"command":"stop_owned_target"})
            io.close(native_server)
            print(json.dumps({"jsonrpc":"2.0","method":"source_contract_revoked","params":{
                "pid":os.getpid(),"owned_holder_handles_remaining":len(holder._owned),
                "clear_before_real_CloseHandle_count":len(cleared),"Native_module_hello_boundary":"synthetic",
                "actual_H_credit":0}}),flush=True)
    finally:
        if plan is not None and isinstance(plan.child,subprocess.Popen):
            if plan.child.poll() is None:plan.child.terminate();plan.child.wait(timeout=10)
            # A successful path already released Popen's process handle.
            if not getattr(plan.child._handle,"closed",False):plan.child._handle.Close()
        if result is not None:result.holder.close()
        remaining=facade.close_all_owned()
        assert remaining["owned_handles_remaining"]==0,remaining


@unittest.skipUnless(os.name=="nt" and os.environ.get("XAR_CANONICAL_OWNED_CHAIN")=="1",
                     "opt-in four owned harmless Python children; no Game/current MCP")
class CanonicalFourChildKernelTest(unittest.TestCase):
    def test_real_pre_resume_three_hops_fresh_origin_unique_DTO_and_revoke(self):
        import win32process,win32job
        executable,env=owned_python_launch_v1();env["XAR_CANONICAL_OWNED_CHAIN"]="1"
        facade=windows.WindowsNativeCustodyFacadeV1(enabled=True,_api=SyntheticNativeReads())
        factory=None;target=None;plan=None;worker=None;job=None;result={}
        with tempfile.TemporaryDirectory(prefix="xar-canonical-source-") as temporary:
            root=Path(temporary);lease=root/"owned-not-native.bin";lease.write_bytes(DATA)
            pipe=r"\\.\pipe\xar_custody_"+secrets.token_hex(24)
            program="import sys,os; from xar_autoplayer.bridge.native_loaded_provider_windows_v1 import WindowsNativeCustodyFacadeV1; from xar_autoplayer.bridge.native_loaded_provider_origin_io_v1 import OriginKernelIOV1; f=WindowsNativeCustodyFacadeV1(enabled=True); i=OriginKernelIOV1(f,enabled=True); h=i.client(sys.argv[1]); i.send(h,{'owned_target_pid':os.getpid()}); assert i.recv(h)=={'command':'stop_owned_target'}; i.close(h); assert f.close_all_owned()['owned_handles_remaining']==0"
            command=[executable,"-B","-c",program,pipe]
            try:
                startup=win32process.STARTUPINFO()
                ph,th,pid,_=win32process.CreateProcess(executable,subprocess.list2cmdline(command),None,None,False,
                    win32process.CREATE_SUSPENDED|subprocess.CREATE_NO_WINDOW|0x400,env,str(root),startup)
                target=runtime._SuspendedWindowsProcess(ph,th,int(pid),command)
                job=runtime._create_kill_on_close_job()
                win32job.AssignProcessToJobObject(job,ph)
                config=runtime.NativeBridgeLaunchConfig("native-headless",pipe,lease,lease)
                factory=chain.CanonicalPreloadFactoryV1(facade=facade,machine_id=MACHINE,
                    expected_dll_sha256=hashlib.sha256(DATA).hexdigest(),
                    entry_source_pins=((str(Path(__file__).resolve()),hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),),
                    enabled=True)
                holder=runtime._apply_pre_native_resume_v1(target,config,factory.pre_native_resume)
                self.assertIs(holder.target,target);self.assertFalse(target.resumed)
                self.assertIs(target._native_preload_custody_v1,holder)
                with self.assertRaises(ValueError):factory.pre_native_resume(target,config)
                original=factory.origin;worker=threading.Thread(target=original.serve,daemon=True);worker.start()
                target.resume()
                plan=chain.prepare_child_v1(holder,role="owner",command=[executable,"-B","-X","utf8",*_actor_program()],
                    env=env,cwd=REPO,entry_source=__file__,enabled=True)
                edge=chain.spawn_owned_popen_v1(plan,stdout=subprocess.DEVNULL,stderr=sys.stderr,
                    after_process_create=lambda child:win32job.AssignProcessToJobObject(job,int(child._handle)))
                original.bind_actual_chain(edge)
                issued=original.io.recv(edge.control)
                self.assertEqual(issued["kind"],"software_issued")
                self.assertTrue(issued["real_stock_Job_member"])
                self.assertEqual(issued["report"]["target_birth_filetime"],str(holder.process.creation_filetime))
                self.assertFalse(issued["report"]["source_verified_flag"])
                self.assertEqual(issued["report"]["SDK_source_epoch"],original.epoch)
                original.revoke_before_close()
                original.io.send(edge.control,{"command":"probe_revocation"})
                completed=original.io.recv(edge.control)
                self.assertEqual(completed["kind"],"chain_finished")
                self.assertEqual(completed["report"]["owned_holder_handles_remaining"],0)
                self.assertGreaterEqual(completed["report"]["clear_before_real_CloseHandle_count"],8)
                original.io.send(edge.control,{"command":"report_ack"})
                self.assertEqual(plan.child.wait(timeout=15),0)
                self.assertEqual(target.wait(timeout=15),0)
                worker.join(timeout=3);self.assertFalse(worker.is_alive())
                initial_job_active=runtime._job_active_processes(job)
                deadline=time.monotonic()+3
                while runtime._job_active_processes(job) and time.monotonic()<deadline:time.sleep(.01)
                self.assertEqual(runtime._job_active_processes(job),0)
                result={"real_owned_created_children":4,"no_current_Game_MCP_Job":True,
                    "pre_resume_target_pid":target.pid,"target_exact_FILETIME":str(holder.process.creation_filetime),
                    "actual_chain":[origin._process_key(p) for _h,p in original.chain],
                    "source_epoch":original.epoch,"issued_software":issued,"revoked":completed,
                    "actual_H_credit":0,"Native_boundary":"synthetic module/hello; real kernel peer and held lease",
                    "target_exit_code":0,"SDKowner_exit_code":0,"own_root_Job_active_processes":0,
                    "own_root_Job_initial_post_wait_active":initial_job_active}
            finally:
                if factory is not None:factory.close()
                if worker is not None:worker.join(timeout=3)
                if job is not None:runtime._close_job(job)
                if plan is not None and plan.child is not None:
                    if plan.child.poll() is None:plan.child.wait(timeout=10)
                    plan.child._handle.Close()
                if target is not None:
                    if target.poll() is None:target.wait(timeout=10)
                    target.close()
                cleanup=facade.close_all_owned()
                self.assertEqual(cleanup["owned_handles_remaining"],0,cleanup)
                self.assertEqual(cleanup["temporary_mappings_remaining"],0,cleanup)
            result["root_cleanup"]=cleanup
        RUNS.append(result);print("CANONICAL_SOURCE_OWNED="+json.dumps(result,separators=(",",":")))


if __name__=="__main__":
    if len(sys.argv)>=2 and sys.argv[1]=="--owned-canonical-role":
        clean,hints=chain.consume_private_bootstrap_args_v1(sys.argv,enabled=True)
        assert clean==[sys.argv[0],"--owned-canonical-role"] and hints is not None
        _run_owned_actor(hints)
    else:unittest.main()
