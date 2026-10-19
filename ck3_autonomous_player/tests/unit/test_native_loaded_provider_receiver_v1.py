"""Local receiver contracts; real kernel test is opt-in and owns every resource."""
import ctypes
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from types import SimpleNamespace
import unittest

from xar_autoplayer.bridge import native_loaded_provider_custody_v1 as custody
from xar_autoplayer.bridge import native_loaded_provider_receiver_v1 as receiver
from xar_autoplayer.bridge import native_loaded_provider_windows_v1 as windows
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.successor_ui_app_owner_v1 import SuccessorUIAppOwner

REPO=Path(__file__).resolve().parents[3]
PIPE=r"\\.\pipe\xar_receiver_source_fixture"
MACHINE="owned-receiver-software-fixture"
BIRTH=134368602545256921
DATA=b"owned receiver source fixture only"
HANDLES={"target":101,"lease":102,"parent":103,"revoke":104}


def owner_for(machine=MACHINE):
    driver=object.__new__(NativeHeadlessGameplayDriver)
    owner=object.__new__(SuccessorUIAppOwner)
    owner.driver,owner.machine,owner.lock=driver,machine,threading.RLock()
    owner.service=SimpleNamespace(driver=driver,_successor_ui_app_owner_v1=owner)
    driver._player_heir_candidate_owner_v1=owner
    owner._player_heir_loaded_provider_v1=None
    owner._player_heir_loaded_custody_v1=None
    owner._player_heir_game_identity_cache_v1=None
    return owner


class KernelFixture:
    """Injected low-level calls, never any WinDLL or actual process observation."""
    def __init__(self):
        self.calls=[];self.closed=[];self.revoked=False;self.fail_close=False
        self.peer=901;self.inherit_failure=None;self.owner=None;self.during_hash=None
    def accept_inherited_handle(self,h):
        self.calls.append(("accept",h))
        if h==self.inherit_failure:raise ValueError("not inherited")
        return h
    def process_identity(self,h):
        self.calls.append(("process",h))
        if h in self.closed:raise OSError("closed")
        return 901,BIRTH,r"C:\synthetic\python.exe",True
    def private_parent_pid(self,h):self.calls.append(("peer",h));return self.peer
    def wait_zero(self,h):self.calls.append(("wait",h));return 0 if self.revoked else 0x102
    def file_identity(self,h):return 77,b"f"*16,len(DATA)
    def final_path(self,h,*,nt):return r"\Device\Volume8\owned.bin" if nt else r"C:\synthetic\owned.bin"
    def hash_held_file(self,h,size):
        if self.during_hash:self.during_hash()
        return hashlib.sha256(DATA).hexdigest()
    def current_process_id(self):return 902
    def close_handle(self,h):
        self.calls.append(("close",h))
        if self.owner:
            assert self.owner._player_heir_loaded_provider_v1 is None
            assert self.owner._player_heir_game_identity_cache_v1 is None
        if self.fail_close:raise OSError("close unknown")
        assert h not in self.closed
        self.closed.append(h)


def stage(fake,**kwargs):
    facade=windows.WindowsNativeCustodyFacadeV1(enabled=True,_api=fake)
    result=receiver.receive_inherited_preload_v1(inherited=dict(HANDLES),owned_control_handle=105,
        facade=facade,machine_id=MACHINE,native_pipe_name=PIPE,enabled=kwargs.pop("enabled",True),**kwargs)
    return facade,result


@unittest.skipUnless(os.name=="nt","Windows path semantics")
class ReceiverContractTests(unittest.TestCase):
    def test_disabled_and_json_location_claims_cannot_create_source(self):
        fake=KernelFixture();facade,result=stage(fake,enabled=False)
        self.assertFalse(result.available);self.assertEqual(fake.calls,[])
        result=receiver.receive_inherited_preload_v1(inherited={"source":"qualified"},
            owned_control_handle=105,facade=facade,machine_id=MACHINE,native_pipe_name=PIPE,enabled=True)
        self.assertFalse(result.available);self.assertEqual(fake.calls,[])

    def test_same_holder_exact_birth_and_local_transfer_never_mint(self):
        fake=KernelFixture();facade,result=stage(fake);self.assertTrue(result.available,result.reason)
        holder=result.holder
        self.assertIs(type(holder),custody._PreloadCustodyV1)
        self.assertIs(holder.seal,custody._RESOURCE_SEAL)
        self.assertEqual(holder.source_role,"received");self.assertIsNone(holder.target)
        self.assertEqual(holder.process.creation_filetime,BIRTH)
        self.assertEqual(holder.process.creation_date,"2026-10-19T05:10:54.5256921Z")
        self.assertFalse(holder._preload_source_verified)
        owner=owner_for();record=receiver.bind_received_owner_v1(result,owner)
        transfer=facade.transfer_readback(holder,record,owner)
        self.assertIs(transfer.source_resource,holder);self.assertEqual(transfer.receiver_pid,902)
        with self.assertRaises(NotImplementedError):facade.transfer_readback(holder,{"claimed":record},owner)
        other=owner_for()
        with self.assertRaises(ValueError):facade.transfer_readback(holder,record,other)
        self.assertFalse(holder.closed)
        issued=custody.issue_loaded_native_provider_v1(custody=holder,owner=owner,driver=owner.driver,
            endpoint=None,transfer=record,os_facade=facade,enabled=True)
        self.assertFalse(issued.issued);self.assertIn("canonical preload continuity",issued.reason)
        self.assertIsNone(owner._player_heir_loaded_provider_v1)
        holder.close();self.assertEqual(set(fake.closed),set(HANDLES.values())|{105})

    def test_wrong_peer_and_noninherited_input_fail_before_file_read(self):
        fake=KernelFixture();fake.peer=999
        facade,result=stage(fake)
        self.assertFalse(result.available);self.assertEqual(set(fake.closed),set(HANDLES.values()))
        self.assertNotIn(105,fake.closed);self.assertEqual(facade._owned,{})
        fake=KernelFixture();fake.inherit_failure=103
        facade,result=stage(fake)
        self.assertFalse(result.available);self.assertEqual(fake.closed,[102,101])
        self.assertNotIn(103,fake.closed)

    def test_root_revocation_clears_owner_before_release_and_unknown_close_is_retained(self):
        fake=KernelFixture();facade,result=stage(fake);owner=owner_for()
        receiver.bind_received_owner_v1(result,owner);fake.owner=owner
        owner._player_heir_loaded_provider_v1=object();owner._player_heir_game_identity_cache_v1=object()
        fake.revoked=True;fake.fail_close=True
        with self.assertRaisesRegex(ValueError,"root revoked"):
            facade.transfer_readback(result.holder,result.transfer,owner)
        self.assertTrue(result.holder.closed);self.assertFalse(result.transfer.active)
        self.assertIs(owner._player_heir_loaded_custody_v1,result.holder)
        self.assertEqual(len(result.holder._owned),5)
        fake.fail_close=False;result.holder.close()
        self.assertIsNone(owner._player_heir_loaded_custody_v1);self.assertEqual(facade._owned,{})

    def test_revocation_during_file_observation_is_not_a_successful_transfer(self):
        fake=KernelFixture();facade,result=stage(fake);owner=owner_for()
        receiver.bind_received_owner_v1(result,owner)
        fake.during_hash=lambda:setattr(fake,"revoked",True)
        with self.assertRaisesRegex(ValueError,"during transfer"):
            facade.transfer_readback(result.holder,result.transfer,owner)
        self.assertTrue(result.holder.closed);self.assertEqual(len(fake.closed),5)

    def test_stage_cleanup_failure_returns_same_unqualified_holder_for_retry(self):
        fake=KernelFixture();fake.revoked=True;fake.fail_close=True
        facade,result=stage(fake)
        self.assertFalse(result.available);self.assertIs(type(result.holder),custody._PreloadCustodyV1)
        self.assertTrue(result.holder.closed);self.assertIsNone(result.transfer)
        self.assertEqual(len(result.holder._owned),5)
        fake.fail_close=False;result.holder.close();self.assertEqual(facade._owned,{})

    def test_parent_generation_change_and_closed_holder_cannot_transfer(self):
        fake=KernelFixture();facade,result=stage(fake);owner=owner_for()
        receiver.bind_received_owner_v1(result,owner)
        result.transfer.parent=replace(result.transfer.parent,creation_filetime=BIRTH+1,
            creation_date=windows._filetime_text(BIRTH+1))
        with self.assertRaisesRegex(ValueError,"parent generation"):
            facade.transfer_readback(result.holder,result.transfer,owner)
        self.assertTrue(result.holder.closed)
        with self.assertRaises((ValueError,NotImplementedError)):
            facade.transfer_readback(result.holder,result.transfer,owner)

    def test_exact_birth_does_not_round_or_change_global_microsecond_parser(self):
        from xar_autoplayer.environment import process_creation_utc
        exact=custody._ProcessReadbackV1(901,BIRTH,windows._filetime_text(BIRTH),r"C:\own\python.exe",True)
        self.assertIs(custody._process(exact),exact)
        with self.assertRaises(ValueError):process_creation_utc(exact.creation_date)
        for text in (windows._filetime_text(BIRTH-1),"20261019051054.525692+000","unknown"):
            with self.subTest(text=text),self.assertRaises(ValueError):
                custody._process(replace(exact,creation_date=text))

    def test_lowlevel_inherited_flags_and_private_client_end_are_required(self):
        from ctypes import wintypes as w
        raw=object.__new__(windows._Win32ReadsV1);raw.c,raw.w=ctypes,w
        calls=[]
        def get_flags(handle,out):ctypes.cast(out,ctypes.POINTER(w.DWORD)).contents.value=1;return 1
        raw.handle_info=get_flags
        raw.handle_flags=lambda *args:calls.append(args) or 1
        self.assertEqual(raw.accept_inherited_handle(101),101);self.assertEqual(calls,[(101,1,0)])
        def info(handle,flags,*args):ctypes.cast(flags,ctypes.POINTER(w.DWORD)).contents.value=0;return 1
        raw.pipe_info=info
        def pid(handle,out):ctypes.cast(out,ctypes.POINTER(w.DWORD)).contents.value=901;return 1
        raw.server_pid=pid
        self.assertEqual(raw.private_parent_pid(105),901)
        def server(handle,flags,*args):ctypes.cast(flags,ctypes.POINTER(w.DWORD)).contents.value=1;return 1
        raw.pipe_info=server
        with self.assertRaisesRegex(ValueError,"client end"):raw.private_parent_pid(105)


def _owned_receiver_child(payload):
    sys.path.insert(0,str(REPO/"tools"))
    from g2_saved_campaign.private_handle_chain_v1 import _Windows
    api=_Windows();control=api.client(payload["pipe"])
    facade=windows.WindowsNativeCustodyFacadeV1(enabled=True)
    result=None
    try:
        result=receiver.receive_inherited_preload_v1(inherited=payload["handles"],
            owned_control_handle=control,facade=facade,machine_id=payload["machine_id"],
            native_pipe_name=PIPE,enabled=True)
        if control in facade._owned:api.owned.remove(control)
        assert result.available,result.reason
        holder=result.holder;owner=owner_for(payload["machine_id"])
        record=receiver.bind_received_owner_v1(result,owner)
        actual=facade.transfer_readback(holder,record,owner)
        denied=custody.issue_loaded_native_provider_v1(custody=holder,owner=owner,driver=owner.driver,
            endpoint=None,transfer=record,os_facade=facade,enabled=True)
        assert not denied.issued and "canonical preload continuity" in denied.reason
        api.send(control,{"status":"local_staged_not_issued","receiver_pid":actual.receiver_pid,
            "target_pid":holder.process.pid,"target_birth_filetime":str(holder.process.creation_filetime),
            "target_birth_iso7":holder.process.creation_date,"source_role":holder.source_role,
            "source_verified":holder._preload_source_verified,"dll_sha256":holder.dll.sha256})
        assert api.recv(control)=={"command":"observe_root_revoke"}
        # A software sentinel proves qualification/cache are cleared before the
        # real owned CloseHandle calls. It is never a minted provider token.
        owner._player_heir_loaded_provider_v1=object();owner._player_heir_game_identity_cache_v1=object()
        close=facade._api.close_handle;checks=[]
        def checked_close(handle):
            assert owner._player_heir_loaded_provider_v1 is None
            assert owner._player_heir_game_identity_cache_v1 is None
            checks.append(handle);close(handle)
        facade._api.close_handle=checked_close
        try:facade.transfer_readback(holder,record,owner)
        except ValueError as error:assert "root revoked" in str(error)
        else:raise AssertionError("revoked root transferred")
        assert holder.closed and len(checks)==5 and not facade._owned
        assert owner._player_heir_loaded_custody_v1 is None
        print(json.dumps({"status":"revoked_cleaned","closed_count":len(checks),
            "remaining":len(facade._owned),"source_token_issued":False}),flush=True)
    finally:
        if result is not None and result.holder is not None:result.holder.close()
        if result is None or control not in getattr(result.holder,"_owned",[]):
            # api owns control only if receiver never accepted it.
            if control in api.owned:api.close(control)
        assert api.cleanup()["owned_remaining"]==0
        assert facade.close_all_owned()["owned_handles_remaining"]==0


@unittest.skipUnless(os.name=="nt" and os.environ.get("XAR_M7_RECEIVER_OWNED")=="1",
                     "opt-in fully owned kernel child; no Game/MCP/Job")
class OwnedReceiverKernelTests(unittest.TestCase):
    def test_inherited_local_holder_exact_filetime_and_root_revocation(self):
        sys.path.insert(0,str(REPO/"tools"))
        from g2_saved_campaign.private_handle_chain_v1 import _Windows
        api=_Windows();process=None;result={};handles={}
        with tempfile.TemporaryDirectory(prefix="xar-m7-receiver-") as directory:
            try:
                path=Path(directory)/"own-lease.bin";path.write_bytes(DATA)
                original=api.own(api.reads.open_read_shared_file(str(path)))
                revoke=api.own(api.event(None,True,False,None))
                handles={"target":api.duplicate(api.reads.current(),inherit=True,access=0x0410|0x100000),
                    "lease":api.duplicate(original,inherit=True),
                    "parent":api.duplicate(api.reads.current(),inherit=True,access=0x1000|0x100000),
                    "revoke":api.duplicate(revoke,inherit=True,access=0x100000)}
                server,name=api.server()
                startup=subprocess.STARTUPINFO(lpAttributeList={"handle_list":list(handles.values())})
                payload={"handles":handles,"pipe":name,"machine_id":"xenoamess-full-tower-eb9d2c1186"}
                from g2_saved_campaign.owned_python_launch_v1 import owned_python_launch_v1
                executable,env=owned_python_launch_v1()
                process=subprocess.Popen([executable,"-B","-X","utf8",str(Path(__file__).resolve()),
                    "--owned-receiver-child",json.dumps(payload)],stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,startupinfo=startup,close_fds=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,env=env)
                child=api.process(int(process._handle))
                for handle in handles.values():api.close(handle)
                api.connected(server)
                self.assertEqual(api.reads.pipe_client_pid(server),process.pid)
                staged=api.recv(server)
                self.assertEqual(staged["status"],"local_staged_not_issued")
                self.assertEqual(staged["receiver_pid"],process.pid)
                self.assertEqual(staged["target_birth_filetime"],api.process(api.reads.current())["birth_filetime"])
                self.assertFalse(staged["source_verified"])
                self.assertEqual(staged["dll_sha256"],hashlib.sha256(DATA).hexdigest())
                api.reads._ok(api.set_event(revoke),"owned root revoke")
                api.send(server,{"command":"observe_root_revoke"})
                out,err=process.communicate(timeout=15)
                self.assertEqual(process.returncode,0,err.decode(errors="replace"))
                final=json.loads(out)
                self.assertEqual(final,{"status":"revoked_cleaned","closed_count":5,"remaining":0,"source_token_issued":False})
                result={"child":child,"stage":staged,"final":final,"exit_code":process.returncode}
            finally:
                if process is not None:
                    if process.poll() is None:process.terminate();process.wait(timeout=10)
                    if process.stdout:process.stdout.close()
                    if process.stderr:process.stderr.close()
                    process._handle.Close()
                cleanup=api.cleanup()
                self.assertEqual(cleanup,{"owned_remaining":0,"errors":[],"temporary_remaining":0})
        result["parent_cleanup"]=cleanup
        print("M7_RECEIVER_OWNED="+json.dumps(result,separators=(",",":")))


if __name__=="__main__":
    if len(sys.argv)==3 and sys.argv[1]=="--owned-receiver-child":
        _owned_receiver_child(json.loads(sys.argv[2]))
    else:unittest.main()
