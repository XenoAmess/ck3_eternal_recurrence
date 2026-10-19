"""Default-OFF Win32 read adapter for the guarded loaded-provider contract.

No production hook or controller-to-SDK handle transfer is installed. Importing
or constructing the disabled adapter loads no Win32 library and opens nothing.
The original runtime process/job and SDK server pipe handles remain borrowed.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import os
import threading
import weakref

from . import native_loaded_provider_custody_v1 as contract


def _normal_dos(path):
    if path.startswith("\\\\?\\UNC\\"):
        path = "\\\\" + path[8:]
    elif path.startswith("\\\\?\\"):
        path = path[4:]
    return contract._path(path)


def _filetime_text(ticks):
    if type(ticks) is not int or not 0 < ticks < 2**64:
        raise ValueError("exact integer kernel FILETIME required")
    seconds, fraction = divmod(ticks, 10000000)
    instant = datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds)
    # Preserve all seven 100 ns digits; local custody checks the integer exactly.
    # Global microsecond identity consumers retain their separate strict limits.
    return instant.strftime("%Y-%m-%dT%H:%M:%S") + f".{fraction:07d}Z"


@dataclass(frozen=True)
class _FileLeaseV1:
    dos_path: str
    nt_path: str
    volume_serial: int
    file_id: bytes
    size: int


class WindowsNativeCustodyFacadeV1(contract._CustodyOSFacadeV1):
    def __init__(self, *, enabled=False, _api=None):
        self.enabled = enabled is True
        self._api = _api
        self._lock = threading.RLock()
        self._owned = {}
        self._files = {}
        self._pipes = {}

    def _os(self):
        if not self.enabled:
            raise NotImplementedError("Windows custody adapter is default OFF")
        if self._api is None:
            self._api = _Win32ReadsV1()
        return self._api

    def duplicate_target_read_handle(self, borrowed_handle):
        with self._lock:
            handle = self._os().duplicate_target_read_handle(borrowed_handle)
            if handle == borrowed_handle or handle in self._owned:
                raise ValueError("new owned read duplicate required")
            self._owned[handle] = "target_read_duplicate"
            return handle

    def open_read_shared_preload_dll(self, path):
        with self._lock:
            api = self._os()
            # No caller-controlled share/access flags and no post-hoc adoption.
            handle = api.open_read_shared_file(contract._path(path))
            if handle in self._owned:
                raise ValueError("fixed opener returned an existing handle")
            self._owned[handle] = "preload_file"
            try:
                volume, identity, size = api.file_identity(handle)
                lease = _FileLeaseV1(_normal_dos(api.final_path(handle, nt=False)),
                    api.final_path(handle, nt=True), volume, identity, size)
                if lease.dos_path != _normal_dos(path):
                    raise ValueError("preload final path differs; no alias qualification")
                self._files[handle] = lease
                return handle
            except Exception:
                # A failed close remains registered for explicit owner cleanup.
                try:
                    self.close_owned_handle(handle)
                except Exception:
                    pass
                raise

    def _lease(self, handle):
        lease = self._files.get(handle)
        if lease is None or self._owned.get(handle) != "preload_file":
            raise ValueError("DLL handle did not come from the fixed pre-load opener")
        api = self._os()
        actual = api.file_identity(handle)
        if (actual != (lease.volume_serial, lease.file_id, lease.size)
                or _normal_dos(api.final_path(handle, nt=False)) != lease.dos_path
                or api.final_path(handle, nt=True).casefold() != lease.nt_path.casefold()):
            raise ValueError("retained pre-load file identity changed")
        return lease

    def observe_dll(self, handle):
        with self._lock:
            lease = self._lease(handle)
            digest = self._os().hash_held_file(handle, lease.size)
            self._lease(handle)
            return contract._DLLReadbackV1(lease.dos_path, lease.volume_serial,
                lease.file_id, digest, lease.size)

    def observe_process(self, handle):
        api = self._os()
        pid, birth, image, alive = api.process_identity(handle)
        return contract._ProcessReadbackV1(pid, birth, _filetime_text(birth),
            _normal_dos(image), alive)

    def observe_modules(self, process_handle):
        with self._lock:
            api = self._os()
            before = api.modules(process_handle)
            result = []
            for base, size, loader_path in before:
                path = _normal_dos(loader_path)
                mapped_nt = api.mapped_file_name(process_handle, base)
                # FileID is derived ONLY from a continuously held pre-load
                # lease with the same kernel mapped filename and full path.
                # Unknown/unrelated modules remain in the complete roster with
                # an unqualified ID; no ordinary path is reopened for evidence.
                matches = []
                for handle, lease in self._files.items():
                    if path == lease.dos_path and mapped_nt.casefold() == lease.nt_path.casefold():
                        matches.append(self._lease(handle))
                if len(matches) > 1:
                    raise ValueError("ambiguous pre-load module lease")
                volume, identity = ((matches[0].volume_serial, matches[0].file_id)
                                    if matches else (0, b""))
                result.append(contract._ModuleReadbackV1(path, base, size, volume, identity))
            # Do not grant a partial or changing module roster. No native call.
            if api.modules(process_handle) != before:
                raise ValueError("module roster changed during OS observation")
            return tuple(result)

    def bind_server_endpoint(self, endpoint):
        """Future adoption-only hook; stores a borrowed actual server instance."""
        self._os()
        from .native_driver import NativeNamedPipeServer, _validate_pipe_name
        if not isinstance(endpoint, NativeNamedPipeServer):
            raise ValueError("canonical SDK server endpoint required")
        handle = endpoint._current_handle()
        if handle is None:
            raise ValueError("current server pipe instance is absent")
        with self._lock:
            self._pipes[handle] = (weakref.ref(endpoint), _validate_pipe_name(endpoint.pipe_name))

    def observe_pipe_client(self, actual_server_handle):
        with self._lock:
            binding = self._pipes.get(actual_server_handle)
            if binding is None:
                raise ValueError("pipe handle was not bound from its actual SDK endpoint")
            endpoint, name = binding[0](), binding[1]
            if endpoint is None or endpoint._current_handle() != actual_server_handle or endpoint.pipe_name != name:
                raise ValueError("server instance or pipe name changed")
            pid = self._os().pipe_client_pid(actual_server_handle)
            if (endpoint._current_handle() != actual_server_handle
                    or endpoint.pipe_name != name):
                raise ValueError("server pipe instance or name changed during kernel peer read")
            return contract._PipeReadbackV1(actual_server_handle, pid, name)

    def current_process_id(self):
        return self._os().current_process_id()

    def transfer_readback(self, resource, transfer, owner):
        record = getattr(self,"_received_preloads_v1",{}).get(resource)
        if record is None or record is not transfer:
            raise NotImplementedError("canonical controller-to-SDK private handle transfer is not implemented")
        from .native_loaded_provider_receiver_v1 import _verified_transfer_v1
        with owner.lock, self._lock:
            return _verified_transfer_v1(self,record,owner)

    def close_owned_handle(self, handle):
        """Pre-adoption abort, or release after custody cleared its owner DTO.

        The facade does not own qualification. Future adopted resources must be
        closed through invalidate_loaded_native_provider_v1, never directly.
        """
        with self._lock:
            if handle not in self._owned:
                raise ValueError("refusing to close borrowed or unknown handle")
            for record in getattr(self,"_received_preloads_v1",{}).values():
                if handle in record.holder._owned:
                    record.active = False
            self._os().close_handle(handle)
            self._owned.pop(handle)
            self._files.pop(handle, None)
            for holder in tuple(getattr(self,"_received_preloads_v1",{})):
                if not any(h in self._owned for h in holder._owned):
                    self._received_preloads_v1.pop(holder)

    def close_all_owned(self):
        """Pre-adoption abort only; not an installed qualification invalidator."""
        errors = []
        with self._lock:
            for handle in tuple(self._owned):
                try:
                    self.close_owned_handle(handle)
                except Exception as error:
                    errors.append(type(error).__name__)
            cleanup = getattr(self._api, "cleanup_temporary_mappings", None)
            temporary = cleanup() if cleanup is not None else {"remaining": 0, "errors": []}
            errors.extend(temporary["errors"])
        return {"owned_handles_remaining": len(self._owned), "release_errors": errors,
                "temporary_mappings_remaining": temporary["remaining"],
                "borrowed_handles_closed": 0, "target_process_control_calls": 0}


class _Win32ReadsV1:
    """Lazy ctypes bindings. No Game PID/path discovery or process termination."""
    PROCESS_READ_ACCESS = 0x0400 | 0x0010 | 0x00100000
    MAX_MODULES = 16384

    def __init__(self):
        if os.name != "nt":
            raise OSError("Win32 custody reads require Windows")
        import ctypes as c
        from ctypes import wintypes as w
        self.c, self.w = c, w
        self._temporary_mappings, self._temporary_views = set(), set()
        self.k = c.WinDLL("kernel32", use_last_error=True)
        self.p = c.WinDLL("psapi", use_last_error=True)
        def bind(lib, name, args, result):
            fn = getattr(lib, name); fn.argtypes, fn.restype = args, result
            return fn
        H, D, P = w.HANDLE, w.DWORD, w.LPVOID
        self.current = bind(self.k,"GetCurrentProcess",[],H)
        self.pid = bind(self.k,"GetCurrentProcessId",[],D)
        self.duplicate = bind(self.k,"DuplicateHandle",[H,H,H,c.POINTER(H),D,w.BOOL,D],w.BOOL)
        self.create = bind(self.k,"CreateFileW",[w.LPCWSTR,D,D,P,D,D,H],H)
        self.close = bind(self.k,"CloseHandle",[H],w.BOOL)
        self.file_info = bind(self.k,"GetFileInformationByHandleEx",[H,c.c_int,P,D],w.BOOL)
        self.file_size = bind(self.k,"GetFileSizeEx",[H,c.POINTER(c.c_longlong)],w.BOOL)
        self.final_name = bind(self.k,"GetFinalPathNameByHandleW",[H,w.LPWSTR,D,D],D)
        self.mapping = bind(self.k,"CreateFileMappingW",[H,P,D,D,D,w.LPCWSTR],H)
        self.view = bind(self.k,"MapViewOfFile",[H,D,D,D,c.c_size_t],P)
        self.unmap = bind(self.k,"UnmapViewOfFile",[P],w.BOOL)
        self.process_id = bind(self.k,"GetProcessId",[H],D)
        self.process_times = bind(self.k,"GetProcessTimes",[H,P,P,P,P],w.BOOL)
        self.process_image = bind(self.k,"QueryFullProcessImageNameW",[H,D,w.LPWSTR,c.POINTER(D)],w.BOOL)
        self.wait = bind(self.k,"WaitForSingleObject",[H,D],D)
        self.enum_modules = bind(self.p,"EnumProcessModulesEx",[H,c.POINTER(H),D,c.POINTER(D),D],w.BOOL)
        self.module_name = bind(self.p,"GetModuleFileNameExW",[H,H,w.LPWSTR,D],D)
        self.module_info = bind(self.p,"GetModuleInformation",[H,H,P,D],w.BOOL)
        self.mapped_name = bind(self.p,"GetMappedFileNameW",[H,P,w.LPWSTR,D],D)
        self.pipe_info = bind(self.k,"GetNamedPipeInfo",[H,c.POINTER(D),P,P,P],w.BOOL)
        self.pipe_pid = bind(self.k,"GetNamedPipeClientProcessId",[H,c.POINTER(D)],w.BOOL)
        self.server_pid = bind(self.k,"GetNamedPipeServerProcessId",[H,c.POINTER(D)],w.BOOL)
        self.handle_info = bind(self.k,"GetHandleInformation",[H,c.POINTER(D)],w.BOOL)
        self.handle_flags = bind(self.k,"SetHandleInformation",[H,D,D],w.BOOL)
        class FileID(c.Structure):
            _fields_=[("volume",c.c_ulonglong),("identity",c.c_ubyte*16)]
        class FT(c.Structure):
            _fields_=[("low",D),("high",D)]
        class ModuleInfo(c.Structure):
            _fields_=[("base",P),("size",D),("entry",P)]
        self.FileID,self.FT,self.ModuleInfo=FileID,FT,ModuleInfo

    def _ok(self, value, label):
        if not value:
            raise self.c.WinError(self.c.get_last_error(), label)
        return value

    def _handle(self, value):
        if isinstance(value, (str, bytes, bool)) or value is None:
            raise TypeError("kernel handle object or integer required")
        return int(value)

    def duplicate_target_read_handle(self, borrowed):
        out=self.w.HANDLE();current=self.current()
        self._ok(self.duplicate(current,self._handle(borrowed),current,self.c.byref(out),self.PROCESS_READ_ACCESS,False,0),"DuplicateHandle(read-only target)")
        return int(out.value)

    def open_read_shared_file(self, path):
        handle=self.create(path,0x80000000,0x1,None,3,0x80,None)
        if handle in (None,0,self.c.c_void_p(-1).value):
            raise self.c.WinError(self.c.get_last_error(),"CreateFile(read,share-read-only)")
        return int(handle)

    def file_identity(self, handle):
        handle=self._handle(handle)
        info=self.FileID();size=self.c.c_longlong()
        self._ok(self.file_info(handle,18,self.c.byref(info),self.c.sizeof(info)),"FileIdInfo")
        self._ok(self.file_size(handle,self.c.byref(size)),"GetFileSizeEx")
        if size.value<=0: raise ValueError("empty DLL file")
        return int(info.volume),bytes(info.identity),int(size.value)

    def _name(self, reader):
        buf=self.c.create_unicode_buffer(32768)
        count=int(reader(buf,len(buf)))
        if count<=0: raise self.c.WinError(self.c.get_last_error(),"kernel full path")
        if count>=len(buf)-1: raise ValueError("kernel path truncated")
        return buf.value

    def final_path(self, handle, *, nt):
        return self._name(lambda buf,size:self.final_name(self._handle(handle),buf,size,2 if nt else 0))

    def hash_held_file(self, handle, size):
        mapping=self._ok(self.mapping(self._handle(handle),None,0x2,0,0,None),"CreateFileMapping(read-only)")
        self._temporary_mappings.add(mapping)
        address=None
        try:
            address=self._ok(self.view(mapping,0x4,0,0,0),"MapViewOfFile(read-only)")
            self._temporary_views.add(address)
            digest=hashlib.sha256()
            for offset in range(0,size,1024*1024):
                digest.update(self.c.string_at(address+offset,min(1024*1024,size-offset)))
            return digest.hexdigest()
        finally:
            try:
                if address:
                    self._ok(self.unmap(address),"UnmapViewOfFile")
                    self._temporary_views.discard(address)
            finally:
                self.close_handle(mapping)

    def process_identity(self, handle):
        handle=self._handle(handle)
        pid=int(self._ok(self.process_id(handle),"GetProcessId"))
        creation,exit_time,kernel,user=(self.FT() for _ in range(4))
        self._ok(self.process_times(handle,self.c.byref(creation),self.c.byref(exit_time),self.c.byref(kernel),self.c.byref(user)),"GetProcessTimes")
        buf=self.c.create_unicode_buffer(32768);size=self.w.DWORD(len(buf))
        self._ok(self.process_image(handle,0,buf,self.c.byref(size)),"QueryFullProcessImageNameW")
        if size.value>=len(buf)-1: raise ValueError("process image path truncated")
        state=int(self.wait(handle,0))
        if state==0xffffffff:raise self.c.WinError(self.c.get_last_error(),"WaitForSingleObject(process,0)")
        if state not in (0,0x102):raise ValueError("unexpected kernel process wait state")
        return pid,(int(creation.high)<<32)|int(creation.low),buf.value,state==0x102

    def modules(self, process):
        process=self._handle(process)
        capacity=1024
        for _ in range(2):
            array=(self.w.HANDLE*capacity)();needed=self.w.DWORD()
            self._ok(self.enum_modules(process,array,self.c.sizeof(array),self.c.byref(needed),3),"EnumProcessModulesEx")
            if needed.value%self.c.sizeof(self.w.HANDLE): raise ValueError("malformed module extent")
            count=needed.value//self.c.sizeof(self.w.HANDLE)
            if count<=capacity:break
            if count>self.MAX_MODULES:raise ValueError("module roster exceeds bound")
            capacity=count
        else:raise ValueError("module roster grew during enumeration")
        rows=[]
        for module in array[:count]:
            info=self.ModuleInfo()
            self._ok(self.module_info(process,module,self.c.byref(info),self.c.sizeof(info)),"GetModuleInformation")
            path=self._name(lambda buf,size:self.module_name(process,module,buf,size))
            rows.append((int(info.base),int(info.size),path))
        return tuple(rows)

    def mapped_file_name(self, process, base):
        return self._name(lambda buf,size:self.mapped_name(self._handle(process),base,buf,size))

    def pipe_client_pid(self, handle):
        handle=self._handle(handle)
        flags=self.w.DWORD();pid=self.w.DWORD()
        self._ok(self.pipe_info(handle,self.c.byref(flags),None,None,None),"GetNamedPipeInfo")
        if not flags.value&1: raise ValueError("handle is not the server end")
        self._ok(self.pipe_pid(handle,self.c.byref(pid)),"GetNamedPipeClientProcessId")
        if not pid.value:raise ValueError("kernel pipe client PID unavailable")
        return int(pid.value)

    def current_process_id(self):
        return int(self.pid())

    def accept_inherited_handle(self, handle):
        handle=self._handle(handle);flags=self.w.DWORD()
        self._ok(self.handle_info(handle,self.c.byref(flags)),"inherited handle flags")
        if not flags.value&1:raise ValueError("handle was not inherited")
        self._ok(self.handle_flags(handle,1,0),"clear inherited handle flag")
        return handle

    def private_parent_pid(self, handle):
        handle=self._handle(handle);flags=self.w.DWORD();pid=self.w.DWORD()
        self._ok(self.pipe_info(handle,self.c.byref(flags),None,None,None),"private client pipe")
        if flags.value&1:raise ValueError("private handoff requires an owned client end")
        self._ok(self.server_pid(handle,self.c.byref(pid)),"private parent pipe PID")
        if not pid.value:raise ValueError("private parent PID unavailable")
        return int(pid.value)

    def wait_zero(self, handle):
        state=int(self.wait(self._handle(handle),0))
        if state==0xffffffff:raise self.c.WinError(self.c.get_last_error(),"received resource wait")
        if state not in (0,0x102):raise ValueError("unexpected received resource wait")
        return state

    def close_handle(self, handle):
        self._ok(self.close(self._handle(handle)),"CloseHandle(owned)")
        self._temporary_mappings.discard(handle)

    def cleanup_temporary_mappings(self):
        errors=[]
        for address in tuple(self._temporary_views):
            try:
                self._ok(self.unmap(address),"UnmapViewOfFile(cleanup)")
                self._temporary_views.remove(address)
            except Exception as error:
                errors.append(type(error).__name__)
        for handle in tuple(self._temporary_mappings):
            try:
                self.close_handle(handle)
            except Exception as error:
                errors.append(type(error).__name__)
        return {"remaining":len(self._temporary_views)+len(self._temporary_mappings),"errors":errors}
