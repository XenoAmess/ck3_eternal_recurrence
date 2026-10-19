"""Injected OS observations only; no Windows API, Game, pipe or DLL is opened."""
from dataclasses import replace
import threading
from types import SimpleNamespace
import unittest

from xar_autoplayer.bridge import native_loaded_provider_custody_v1 as custody
from xar_autoplayer.bridge import player_heir_candidate_component_v1 as component
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver, NativeNamedPipeServer, NativeProtocolState
from xar_autoplayer.bridge.successor_ui_app_owner_v1 import SuccessorUIAppOwner
from xar_autoplayer.runtime import _SuspendedWindowsProcess

PIPE = r"\\.\pipe\xar_loaded_provider_fixture"
IMAGE = r"C:\synthetic\ck3.exe"
DLL = r"C:\synthetic\native30.dll"
DLL_SHA = "a" * 64
FILETIME = 134368602545256920


class Handle:
    def __init__(self, name): self.name = name
    def __repr__(self): return self.name


class Transfer:
    pass


class Facade(custody._CustodyOSFacadeV1):
    def __init__(self):
        self.original = Handle("borrowed runtime target")
        self.target = Handle("owned target duplicate")
        self.dll = Handle("owned fixed-mode preload DLL")
        self.received_target = Handle("SDK target duplicate")
        self.received_dll = Handle("SDK DLL duplicate")
        self.pipe = Handle("SDK actual server pipe")
        self.transfer = Transfer()
        self.calls, self.closed = [], []
        self.loaded = False
        self.game = custody._ProcessReadbackV1(123, FILETIME, "20261019051054.525692+000", IMAGE, True)
        self.file = custody._DLLReadbackV1(DLL, 47, b"f" * 16, DLL_SHA, 18000000)
        self.received_file = None
        self.module = custody._ModuleReadbackV1(DLL, 0x7FFA12340000, 19000000, 47, b"f" * 16)
        self.extra_modules = ()
        self.peer_pid, self.receiver_pid = 123, 9001
        self.module_hook = None
        self.close_error = False
        self.owner = None

    def duplicate_target_read_handle(self, handle):
        self.calls.append("duplicate_target")
        if handle is not self.original: raise ValueError("foreign borrowed handle")
        return self.target

    def open_read_shared_preload_dll(self, path):
        # This fake models the fixed producer, not a caller's share-mode flag.
        self.calls.append("fixed_read_share_read_open")
        return self.dll

    def observe_process(self, handle):
        self.calls.append("kernel_process")
        if handle in self.closed or handle not in (self.original, self.target, self.received_target):
            raise OSError("invalid process handle")
        return self.game

    def observe_dll(self, handle):
        self.calls.append("held_file_identity_and_hash")
        if handle in self.closed: raise OSError("closed DLL handle")
        if handle is self.received_dll: return self.received_file or self.file
        if handle is self.dll: return self.file
        raise OSError("foreign file handle")

    def observe_modules(self, handle):
        self.calls.append("mapped_module_identity")
        if self.module_hook: self.module_hook()
        return ((self.module,) if self.loaded else ()) + self.extra_modules

    def transfer_readback(self, resource, transfer, owner):
        self.calls.append("actual_handle_transfer")
        if transfer is not self.transfer: raise ValueError("not the canonical transfer")
        return custody._TransferReadbackV1(resource, owner, self.receiver_pid,
            self.received_target, self.received_dll)

    def current_process_id(self): return 9001

    def observe_pipe_client(self, handle):
        self.calls.append("kernel_pipe_client")
        if handle is not self.pipe: raise ValueError("wrong current pipe")
        return custody._PipeReadbackV1(handle, self.peer_pid, PIPE)

    def close_owned_handle(self, handle):
        self.calls.append("close_owned")
        if handle is self.original: raise AssertionError("must not close runtime handle")
        if self.owner is not None:
            assert self.owner._player_heir_loaded_provider_v1 is None
        if self.close_error: raise OSError("synthetic unverified close")
        if handle in self.closed: raise AssertionError("double close")
        self.closed.append(handle)


def context():
    facade = Facade()
    target = object.__new__(_SuspendedWindowsProcess)
    target._process_handle, target._thread_handle = facade.original, Handle("primary thread")
    target.pid, target.args, target.resumed, target.returncode = 123, [IMAGE], False, None
    driver = object.__new__(NativeHeadlessGameplayDriver)
    endpoint = object.__new__(NativeNamedPipeServer)
    endpoint.pipe_name, endpoint._handle_lock, endpoint._handle = PIPE, threading.Lock(), facade.pipe
    driver.endpoint, driver.pipe_name, driver._session_bridge_pid = endpoint, PIPE, 123
    driver.state = NativeProtocolState(PIPE)
    driver.state.ingest(dict(type="hello", protocol_version=1, pid=123, capabilities=[], connection_generation=3))
    owner = object.__new__(SuccessorUIAppOwner)
    owner.driver, owner.machine, owner.lock = driver, "software-fixture-machine", threading.RLock()
    owner.service = SimpleNamespace(driver=driver, _successor_ui_app_owner_v1=owner)
    owner._player_heir_loaded_provider_v1 = None
    driver._player_heir_candidate_owner_v1 = owner
    return facade, target, owner, driver, endpoint


def prepare(facade, target, **kwargs):
    return custody.prepare_canonical_cold_custody_v1(target=target, dll_path=DLL,
        expected_dll_sha256=kwargs.pop("sha", DLL_SHA), machine_id="software-fixture-machine",
        pipe_name=PIPE, os_facade=facade, enabled=kwargs.pop("enabled", True), **kwargs)


def issue(resource, owner, driver, endpoint, facade, **kwargs):
    return custody.issue_loaded_native_provider_v1(custody=resource, owner=owner, driver=driver,
        endpoint=endpoint, transfer=kwargs.pop("transfer", facade.transfer), os_facade=facade,
        enabled=kwargs.pop("enabled", True), **kwargs)


class GuardedIssuerTests(unittest.TestCase):
    def test_default_off_and_missing_real_inputs_do_no_os_work(self):
        f, target, owner, driver, endpoint = context()
        self.assertIsNone(prepare(f, target, enabled=False))
        result = custody.issue_loaded_native_provider_v1(custody=None, owner=owner, driver=driver,
            endpoint=endpoint, transfer=None, os_facade=f)
        self.assertFalse(result.issued)
        self.assertFalse(issue(None, owner, driver, endpoint, f).issued)
        self.assertFalse(issue({"native_dll_sha256": DLL_SHA}, owner, driver, endpoint, f).issued)
        self.assertIsNone(custody.prepare_canonical_cold_custody_v1(target=target,
            dll_path=DLL, expected_dll_sha256=DLL_SHA, machine_id="software-fixture-machine",
            pipe_name=PIPE, os_facade=custody._CustodyOSFacadeV1(), enabled=True))
        self.assertEqual(f.calls, [])
        self.assertIsNone(owner._player_heir_loaded_provider_v1)

    def test_same_integer_birth_and_verified_chain_mints_only_existing_M7_DTO(self):
        f, target, owner, driver, endpoint = context()
        resource = prepare(f, target)
        self.assertIsNotNone(resource)
        self.assertIn("fixed_read_share_read_open", f.calls)
        f.game = replace(f.game, creation_date="20261019131054.525692+480")
        f.loaded, target.resumed = True, True
        result = issue(resource, owner, driver, endpoint, f)
        self.assertTrue(result.issued, result)
        provider = owner._player_heir_loaded_provider_v1
        self.assertIs(type(provider), component._LoadedNativeProviderV1)
        self.assertIs(provider.seal, component._LOADED_NATIVE_SEAL)
        self.assertEqual(provider.native_dll_sha256, DLL_SHA)
        self.assertEqual((provider.game_pid, provider.connection_generation), (123, 3))
        self.assertEqual(provider.game_birth, "20261019051054.525692+000")
        self.assertEqual(provider.game_creation_filetime, FILETIME)
        self.assertIs(owner._player_heir_loaded_custody_v1, resource)
        self.assertEqual(f.closed, [])
        f.owner = owner
        closed = custody.invalidate_loaded_native_provider_v1(owner, reason="actual_disconnect")
        self.assertFalse(closed.issued)
        self.assertEqual(set(f.closed), {f.target, f.dll, f.received_target, f.received_dll})
        self.assertNotIn(f.original, f.closed)
        self.assertIsNone(owner._player_heir_loaded_provider_v1)
        self.assertIsNone(owner._player_heir_loaded_custody_v1)
        custody.invalidate_loaded_native_provider_v1(owner)
        self.assertEqual(len(f.closed), 4)

    def test_local_exact_100ns_type_is_carried_without_rounding_global_identity(self):
        from xar_autoplayer.bridge.native_loaded_provider_windows_v1 import _filetime_text
        from xar_autoplayer.environment import process_creation_utc
        f,target,owner,driver,endpoint=context()
        f.game=replace(f.game,creation_filetime=FILETIME+1,creation_date=_filetime_text(FILETIME+1))
        resource=prepare(f,target)
        self.assertIsNotNone(resource)
        f.loaded,target.resumed=True,True
        self.assertTrue(issue(resource,owner,driver,endpoint,f).issued)
        provider=owner._player_heir_loaded_provider_v1
        self.assertEqual(provider.game_creation_filetime,FILETIME+1)
        self.assertEqual(provider.game_birth,"2026-10-19T05:10:54.5256921Z")
        with self.assertRaises(ValueError):process_creation_utc(provider.game_birth)
        custody.invalidate_loaded_native_provider_v1(owner)

    def test_preload_rejects_posthoc_or_ambiguous_sources_before_any_issuance(self):
        def resumed(f,t): t.resumed = True
        def precision(f,t): f.game = replace(f.game, creation_filetime=FILETIME+1)
        def source_hash(f,t): f.file = replace(f.file, sha256=component.GETTER_SOURCE_CLOSURE_SHA256)
        def preloaded(f,t): f.loaded = True
        for mutate in (resumed, precision, source_hash, preloaded):
            with self.subTest(mutate=mutate.__name__):
                f,t,owner,driver,endpoint = context(); mutate(f,t)
                self.assertIsNone(prepare(f,t))
                self.assertIsNone(owner._player_heir_loaded_provider_v1)
                self.assertNotIn(f.original, f.closed)
        f,t,owner,driver,endpoint = context()
        self.assertIsNone(prepare(f,t,sha=component.GETTER_SOURCE_CLOSURE_SHA256))
        self.assertEqual(f.calls, [])
        self.assertIsNone(prepare(f, {"pid": 123}))
        self.assertEqual(f.calls, [])

    def test_missing_transfer_or_public_JSON_cannot_complete_preload_custody(self):
        f,t,owner,driver,endpoint = context(); resource=prepare(f,t); f.loaded=True
        f.calls.clear()
        for transfer in (None, {}, {"exitcode":0,"DLLsha":DLL_SHA}, 123, "owned"):
            with self.subTest(transfer=transfer):
                self.assertFalse(issue(resource,owner,driver,endpoint,f,transfer=transfer).issued)
                self.assertIsNone(owner._player_heir_loaded_provider_v1)
        self.assertEqual(f.calls, [])
        resource.close()

    def test_actual_readback_mismatches_and_connection_race_stay_unknown(self):
        def wrong_peer(f,t,o,d,e): f.peer_pid=999
        def wrong_birth(f,t,o,d,e): f.game=replace(f.game,creation_filetime=FILETIME+10,creation_date="20261019051054.525693+000")
        def wrong_image(f,t,o,d,e): f.game=replace(f.game,executable=r"C:\foreign\ck3.exe")
        def replaced_file(f,t,o,d,e): f.file=replace(f.file,file_id=b"g"*16)
        def replaced_transfer_file(f,t,o,d,e): f.received_file=replace(f.file,file_id=b"g"*16)
        def wrong_module_id(f,t,o,d,e): f.module=replace(f.module,file_id=b"g"*16)
        def wrong_module_path(f,t,o,d,e): f.module=replace(f.module,path=r"C:\foreign\native30.dll")
        def namesake(f,t,o,d,e): f.extra_modules=(replace(f.module,path=r"C:\foreign\native30.dll"),)
        def wrong_receiver(f,t,o,d,e): f.receiver_pid=9002
        def pipe_race(f,t,o,d,e): f.module_hook=lambda:setattr(e,"_handle",Handle("new instance"))
        def generation_race(f,t,o,d,e):
            f.module_hook=lambda:d.state.ingest(dict(type="hello",protocol_version=1,pid=123,capabilities=[],connection_generation=4))
        def closed_source(f,t,o,d,e): f.closed.append(f.dll)
        for mutate in (wrong_peer,wrong_birth,wrong_image,replaced_file,replaced_transfer_file,
                       wrong_module_id,wrong_module_path,namesake,wrong_receiver,pipe_race,generation_race,closed_source):
            with self.subTest(mutate=mutate.__name__):
                f,t,o,d,e=context(); resource=prepare(f,t); f.loaded=True
                mutate(f,t,o,d,e)
                result=issue(resource,o,d,e,f)
                self.assertFalse(result.issued,result)
                self.assertIsNone(o._player_heir_loaded_provider_v1)
                self.assertNotIn(f.original,f.closed)
                if mutate is wrong_peer:
                    self.assertIs(o._player_heir_loaded_custody_v1,resource)
                    f.owner=o
                    custody.invalidate_loaded_native_provider_v1(o)
                    self.assertEqual(len(f.closed),4)

    def test_failed_requalification_revokes_previous_DTO_but_retains_cleanup_owner(self):
        f,t,o,d,e=context(); resource=prepare(f,t); f.loaded=True
        self.assertTrue(issue(resource,o,d,e,f).issued)
        f.calls.clear()
        self.assertFalse(issue(resource,o,d,e,f,transfer=None).issued)
        self.assertEqual(f.calls,[])
        self.assertIsNone(o._player_heir_loaded_provider_v1)
        self.assertIs(o._player_heir_loaded_custody_v1,resource)
        f.owner=o
        custody.invalidate_loaded_native_provider_v1(o)
        self.assertEqual(len(f.closed),4)

    def test_unverified_close_keeps_resource_without_retaining_qualification(self):
        f,t,o,d,e=context(); resource=prepare(f,t); f.loaded=True
        self.assertTrue(issue(resource,o,d,e,f).issued)
        f.owner=o; f.close_error=True
        result=custody.invalidate_loaded_native_provider_v1(o)
        self.assertIn("unverified",result.reason)
        self.assertIsNone(o._player_heir_loaded_provider_v1)
        self.assertIs(o._player_heir_loaded_custody_v1,resource)
        self.assertEqual(len(resource._owned),4)
        f.close_error=False
        custody.invalidate_loaded_native_provider_v1(o)
        self.assertIsNone(o._player_heir_loaded_custody_v1)


if __name__ == "__main__":
    unittest.main()
