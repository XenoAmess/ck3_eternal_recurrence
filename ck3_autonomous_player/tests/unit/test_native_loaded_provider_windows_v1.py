"""Injected low-level API only: no Win32 API, DLL or process is opened."""
import ctypes
from ctypes import wintypes
import hashlib
import os
import threading
import unittest
from unittest.mock import patch

from xar_autoplayer.bridge import native_loaded_provider_windows_v1 as adapter
from xar_autoplayer.bridge import native_loaded_provider_custody_v1 as contract
from xar_autoplayer.bridge.native_driver import NativeNamedPipeServer

DOS = r"C:\synthetic\native30.dll"
NT = r"\Device\HarddiskVolume8\synthetic\native30.dll"
IMAGE = r"C:\synthetic\python.exe"
PIPE = r"\\.\pipe\xar_adapter_fixture"
FILETIME = 134368602545256920
DATA = b"tiny owned software fixture only"


class FakeAPI:
    def __init__(self):
        self.calls, self.closed = [], []
        self.volume, self.identity, self.size = 79, b"i"*16, len(DATA)
        self.dos, self.nt = DOS, NT
        self.module_rows = ((0x12340000, 4096, DOS),)
        self.mapped = NT
        self.module_count = 0
        self.roster_race = False
        self.close_fail = False
        self.on_peer = None

    def duplicate_target_read_handle(self, h):
        self.calls.append(("duplicate_read",h)); return 201
    def open_read_shared_file(self,path):
        self.calls.append(("fixed_open",path)); return 101
    def file_identity(self,h):
        self.calls.append(("file_id",h)); return self.volume,self.identity,self.size
    def final_path(self,h,*,nt):
        self.calls.append(("final_path",h,nt)); return self.nt if nt else "\\\\?\\"+self.dos
    def hash_held_file(self,h,size):
        self.calls.append(("hash_same_handle",h,size)); return hashlib.sha256(DATA).hexdigest()
    def process_identity(self,h):
        self.calls.append(("process_kernel",h)); return 901,FILETIME,IMAGE,True
    def modules(self,h):
        self.calls.append(("module_roster",h));self.module_count+=1
        if self.roster_race and self.module_count%2==0:return ()
        return self.module_rows
    def mapped_file_name(self,h,base):
        self.calls.append(("kernel_mapping_path",h,base));return self.mapped
    def pipe_client_pid(self,h):
        self.calls.append(("kernel_server_peer",h))
        if self.on_peer:self.on_peer()
        return 901
    def current_process_id(self):return 902
    def close_handle(self,h):
        self.calls.append(("close_owned",h))
        if self.close_fail:raise OSError("synthetic close unknown")
        self.closed.append(h)


def endpoint(handle=301):
    value=object.__new__(NativeNamedPipeServer)
    value._handle,value._handle_lock,value.pipe_name=handle,threading.Lock(),PIPE
    return value


@unittest.skipUnless(os.name=="nt","Windows path/ABI adapter")
class WindowsAdapterContractTests(unittest.TestCase):
    def test_disabled_is_lazy_and_cannot_be_enabled_by_issuer_flag_alone(self):
        fake=FakeAPI();value=adapter.WindowsNativeCustodyFacadeV1(_api=fake)
        with patch.object(adapter,"_Win32ReadsV1",side_effect=AssertionError("must remain lazy")):
            for operation in (lambda:value.open_read_shared_preload_dll(DOS),
                              lambda:value.observe_process(1),lambda:value.bind_server_endpoint(endpoint())):
                with self.assertRaises(NotImplementedError):operation()
        self.assertEqual(fake.calls,[])
        self.assertEqual(value.close_all_owned()["owned_handles_remaining"],0)

    def test_exact_held_file_hash_and_file_id_without_path_reopen(self):
        fake=FakeAPI();value=adapter.WindowsNativeCustodyFacadeV1(enabled=True,_api=fake)
        handle=value.open_read_shared_preload_dll(DOS)
        observed=value.observe_dll(handle)
        self.assertIs(type(observed),contract._DLLReadbackV1)
        self.assertEqual((observed.volume_serial,observed.file_id),(79,b"i"*16))
        self.assertEqual(observed.sha256,hashlib.sha256(DATA).hexdigest())
        self.assertEqual(sum(call[0]=="fixed_open" for call in fake.calls),1)
        self.assertIn(("hash_same_handle",handle,len(DATA)),fake.calls)
        with self.assertRaises(ValueError):value.observe_dll(999)
        self.assertEqual(value.close_all_owned()["owned_handles_remaining"],0)

    def test_module_identity_requires_both_kernel_mapping_and_live_preload_file(self):
        fake=FakeAPI();value=adapter.WindowsNativeCustodyFacadeV1(enabled=True,_api=fake)
        # Post-hoc module paths alone never acquire a qualified FileID.
        self.assertEqual(value.observe_modules(201)[0].file_id,b"")
        value.open_read_shared_preload_dll(DOS)
        self.assertEqual(value.observe_modules(201)[0].file_id,b"i"*16)
        fake.mapped=r"\Device\HarddiskVolume8\foreign\native30.dll"
        self.assertEqual(value.observe_modules(201)[0].file_id,b"")
        fake.mapped=NT;fake.identity=b"x"*16
        with self.assertRaisesRegex(ValueError,"identity changed"):value.observe_modules(201)
        value.close_all_owned()

    def test_all_modules_are_kept_and_changing_roster_is_refused(self):
        fake=FakeAPI();value=adapter.WindowsNativeCustodyFacadeV1(enabled=True,_api=fake)
        value.open_read_shared_preload_dll(DOS)
        fake.module_rows += ((0x23450000,8192,r"C:\foreign\native30.dll"),)
        self.assertEqual(len(value.observe_modules(201)),2)
        fake.roster_race=True;fake.module_count=0
        with self.assertRaisesRegex(ValueError,"roster changed"):value.observe_modules(201)
        value.close_all_owned()

    def test_kernel_birth_preserves_seventh_digit_and_never_uses_float(self):
        fake=FakeAPI();value=adapter.WindowsNativeCustodyFacadeV1(enabled=True,_api=fake)
        game=value.observe_process(201)
        self.assertEqual(game.creation_filetime,FILETIME)
        self.assertEqual(game.creation_date,"2026-10-19T05:10:54.5256920Z")
        self.assertEqual(adapter._filetime_text(FILETIME+1),"2026-10-19T05:10:54.5256921Z")
        exact=contract._ProcessReadbackV1(901,FILETIME+1,
            adapter._filetime_text(FILETIME+1),IMAGE,True)
        self.assertIs(contract._process(exact),exact)
        from xar_autoplayer.environment import process_creation_utc
        with self.assertRaises(ValueError):process_creation_utc(exact.creation_date)
        with self.assertRaises(ValueError):
            contract._process(contract._ProcessReadbackV1(901,FILETIME+1,
                game.creation_date,IMAGE,True))

    def test_peer_comes_from_bound_current_server_and_never_owns_its_handle(self):
        fake=FakeAPI();value=adapter.WindowsNativeCustodyFacadeV1(enabled=True,_api=fake)
        ep=endpoint()
        with self.assertRaises(ValueError):value.observe_pipe_client(301)
        value.bind_server_endpoint(ep)
        peer=value.observe_pipe_client(301)
        self.assertEqual((peer.handle,peer.client_pid,peer.name),(301,901,PIPE))
        with self.assertRaises(ValueError):value.close_owned_handle(301)
        fake.on_peer=lambda:setattr(ep,"_handle",302)
        with self.assertRaisesRegex(ValueError,"instance or name changed"):value.observe_pipe_client(301)
        ep._handle=301
        fake.on_peer=lambda:setattr(ep,"pipe_name",PIPE+"_foreign")
        with self.assertRaisesRegex(ValueError,"instance or name changed"):value.observe_pipe_client(301)
        with self.assertRaises(ValueError):value.bind_server_endpoint({"pipe":PIPE,"handle":301})
        self.assertNotIn(301,fake.closed)

    def test_only_own_duplicates_are_closed_and_failed_release_remains_owned(self):
        fake=FakeAPI();value=adapter.WindowsNativeCustodyFacadeV1(enabled=True,_api=fake)
        self.assertEqual(value.duplicate_target_read_handle(900),201)
        value.open_read_shared_preload_dll(DOS)
        with self.assertRaises(ValueError):value.close_owned_handle(900)
        fake.close_fail=True
        result=value.close_all_owned()
        self.assertEqual(result["owned_handles_remaining"],2)
        self.assertEqual(len(result["release_errors"]),2)
        fake.close_fail=False
        self.assertEqual(value.close_all_owned()["owned_handles_remaining"],0)
        self.assertEqual(set(fake.closed),{101,201})
        self.assertNotIn(900,fake.closed)

    def test_transfer_stays_explicitly_unimplemented_even_with_enabled_adapter(self):
        fake=FakeAPI();value=adapter.WindowsNativeCustodyFacadeV1(enabled=True,_api=fake)
        with self.assertRaisesRegex(NotImplementedError,"transfer is not implemented"):
            value.transfer_readback(object(),{"claimed":"actual"},object())
        self.assertEqual(fake.calls,[])

    def test_concrete_fixed_CreateFile_arguments_and_read_only_duplicate_rights(self):
        # Exercise the concrete wrapper body with a fake function pointer; do
        # not instantiate _Win32ReadsV1 or call any Windows function.
        raw=object.__new__(adapter._Win32ReadsV1)
        raw.c,raw.w=ctypes,wintypes
        calls=[]
        raw.create=lambda *args:calls.append(args) or 123
        self.assertEqual(raw.open_read_shared_file(DOS),123)
        self.assertEqual(calls[0],(DOS,0x80000000,1,None,3,0x80,None))
        raw.current=lambda:-1
        def duplicate(*args):
            calls.append(args)
            ctypes.cast(args[3],ctypes.POINTER(wintypes.HANDLE)).contents.value=124
            return 1
        raw.duplicate=duplicate
        self.assertEqual(raw.duplicate_target_read_handle(900),124)
        self.assertEqual(calls[-1][4:],(0x0400|0x0010|0x00100000,False,0))

    def test_same_handle_mapping_hash_keeps_failed_temporary_release_diagnostic(self):
        raw=object.__new__(adapter._Win32ReadsV1)
        raw.c,raw.w=ctypes,wintypes
        raw._temporary_mappings,raw._temporary_views=set(),set()
        buf=ctypes.create_string_buffer(DATA)
        calls=[]
        raw.mapping=lambda *args:calls.append(("map",args)) or 600
        raw.view=lambda *args:ctypes.addressof(buf)
        raw.unmap=lambda address:calls.append(("unmap",address)) or 1
        raw.close=lambda handle:calls.append(("close",handle)) or 1
        self.assertEqual(raw.hash_held_file(101,len(DATA)),hashlib.sha256(DATA).hexdigest())
        self.assertEqual(calls[0],("map",(101,None,2,0,0,None)))
        self.assertEqual(raw.cleanup_temporary_mappings(),{"remaining":0,"errors":[]})
        raw.unmap=lambda address:(_ for _ in ()).throw(OSError("synthetic unmap unknown"))
        with self.assertRaises(OSError):raw.hash_held_file(101,len(DATA))
        self.assertEqual(len(raw._temporary_views),1)
        raw.unmap=lambda address:1
        self.assertEqual(raw.cleanup_temporary_mappings(),{"remaining":0,"errors":[]})

    def test_concrete_pipe_reader_rejects_client_end_before_kernel_peer_read(self):
        raw=object.__new__(adapter._Win32ReadsV1)
        raw.c,raw.w=ctypes,wintypes
        calls=[]
        def pipe_info(handle,flags,*unused):
            ctypes.cast(flags,ctypes.POINTER(wintypes.DWORD)).contents.value=0
            return 1
        def pipe_pid(handle,out):
            calls.append(handle)
            ctypes.cast(out,ctypes.POINTER(wintypes.DWORD)).contents.value=901
            return 1
        raw.pipe_info,raw.pipe_pid=pipe_info,pipe_pid
        with self.assertRaisesRegex(ValueError,"not the server end"):raw.pipe_client_pid(301)
        self.assertEqual(calls,[])
        def server_info(handle,flags,*unused):
            ctypes.cast(flags,ctypes.POINTER(wintypes.DWORD)).contents.value=1
            return 1
        raw.pipe_info=server_info
        self.assertEqual(raw.pipe_client_pid(301),901)
        self.assertEqual(calls,[301])

    def test_concrete_process_liveness_uses_zero_timeout_kernel_wait(self):
        raw=object.__new__(adapter._Win32ReadsV1)
        raw.c,raw.w=ctypes,wintypes
        class FT(ctypes.Structure):
            _fields_=[("low",wintypes.DWORD),("high",wintypes.DWORD)]
        raw.FT=FT
        raw.process_id=lambda handle:901
        def times(handle,creation,*unused):
            value=ctypes.cast(creation,ctypes.POINTER(FT)).contents
            value.low,value.high=FILETIME&0xffffffff,FILETIME>>32
            return 1
        def image(handle,flags,buf,size):
            buf.value=IMAGE
            ctypes.cast(size,ctypes.POINTER(wintypes.DWORD)).contents.value=len(IMAGE)
            return 1
        raw.process_times,raw.process_image=times,image
        calls=[]
        raw.wait=lambda handle,timeout:calls.append((handle,timeout)) or 0x102
        self.assertTrue(raw.process_identity(201)[3])
        # A signaled process is dead regardless of its application exit value.
        raw.wait=lambda handle,timeout:calls.append((handle,timeout)) or 0
        self.assertFalse(raw.process_identity(201)[3])
        self.assertEqual(calls,[(201,0),(201,0)])


if __name__=="__main__":
    unittest.main()
