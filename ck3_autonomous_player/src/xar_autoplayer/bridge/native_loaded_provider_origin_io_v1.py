"""Private, bounded kernel transport for default-OFF canonical custody.

Messages locate resources and request observations; they are never tokens.
No PID discovery, Game command, arbitrary handle opening or process termination.
"""
import ctypes
from ctypes import wintypes as w
import json
import secrets
import time

from . import native_loaded_provider_custody_v1 as contract
from .native_loaded_provider_windows_v1 import WindowsNativeCustodyFacadeV1


class OriginKernelIOV1:
    def __init__(self, facade, *, enabled=False, timeout=10.0):
        if enabled is not True:
            raise NotImplementedError("canonical origin transport is default OFF")
        contract._require(type(facade) is WindowsNativeCustodyFacadeV1 and facade.enabled,
                          "actual Windows custody facade required")
        contract._require(type(timeout) in (int,float) and 0<timeout<=30,"bounded private timeout required")
        self.facade,self.api,self.timeout=facade,facade._os(),timeout
        self.rx={};self._holders={}
        kernel=self.api.k
        def bind(name,args,result):
            f=getattr(kernel,name);f.argtypes,f.restype=args,result;return f
        H,D,P=w.HANDLE,w.DWORD,w.LPVOID
        self._event=bind("CreateEventW",[P,w.BOOL,w.BOOL,w.LPCWSTR],H)
        self._set_event=bind("SetEvent",[H],w.BOOL)
        self._pipe=bind("CreateNamedPipeW",[w.LPCWSTR,D,D,D,D,D,D,P],H)
        self._connect=bind("ConnectNamedPipe",[H,P],w.BOOL)
        self._peek=bind("PeekNamedPipe",[H,P,D,P,ctypes.POINTER(D),P],w.BOOL)
        self._read=bind("ReadFile",[H,P,D,ctypes.POINTER(D),P],w.BOOL)
        self._write=bind("WriteFile",[H,P,D,ctypes.POINTER(D),P],w.BOOL)

    def own(self, handle, *, holder=None, kind="origin_transport"):
        handle=int(handle or 0)
        contract._require(handle not in (0,ctypes.c_void_p(-1).value),"invalid private resource")
        with self.facade._lock:
            contract._require(handle not in self.facade._owned,"private resource already owned")
            self.facade._owned[handle]=kind
            if holder is not None:
                holder._owned.append(handle);self._holders[handle]=holder
        return handle

    def adopt_inherited(self,handle,*,holder):
        self.api.accept_inherited_handle(handle)
        return self.own(handle,holder=holder,kind="origin_inherited")

    def duplicate(self,handle,*,holder=None,inherit=False,access=None):
        out=w.HANDLE();current=self.api.current()
        self.api._ok(self.api.duplicate(current,int(handle),current,ctypes.byref(out),
            0 if access is None else access,inherit,2 if access is None else 0),"private read duplicate")
        return self.own(out.value,holder=holder,kind="origin_duplicate")

    def pull_read_process(self,actual_child_handle,remote_location,*,holder):
        contract._require(type(remote_location) is int and remote_location>0,"remote handle location required")
        out=w.HANDLE()
        # actual_child_handle belongs to an actual returned child, supplied by
        # the private creator record. It is not opened from a message PID.
        self.api._ok(self.api.duplicate(int(actual_child_handle),remote_location,self.api.current(),
            ctypes.byref(out),self.api.PROCESS_READ_ACCESS,False,0),"upward actual-child read duplicate")
        result=self.own(out.value,holder=holder,kind="origin_pulled_process")
        contract._process(self.facade.observe_process(result))
        return result

    def event(self,*,holder):
        return self.own(self._event(None,True,False,None),holder=holder,kind="origin_revoke_event")

    def revoke(self,event):
        self.api._ok(self._set_event(event),"canonical origin revoke")

    def server(self,*,holder=None,name=None):
        name=name or r"\\.\pipe\xar_custody_"+secrets.token_hex(24)
        contract._require(isinstance(name,str) and name.startswith(r"\\.\pipe\xar_custody_"),
                          "private canonical server name required")
        # First, local-only, nonblocking instance; server is never inherited.
        return self.own(self._pipe(name,3|0x80000,1|8,1,32768,32768,1000,None),
                        holder=holder,kind="origin_server"),name

    def client(self,name,*,holder=None):
        contract._require(isinstance(name,str) and name.startswith(r"\\.\pipe\xar_custody_"),
                          "private canonical pipe required")
        deadline=time.monotonic()+self.timeout
        while True:
            handle=self.api.create(name,0xC0000000,0,None,3,0,None)
            if handle not in (None,0,ctypes.c_void_p(-1).value):
                return self.own(handle,holder=holder,kind="origin_client")
            error=ctypes.get_last_error()
            if error not in (2,231) or time.monotonic()>deadline:raise ctypes.WinError(error)
            time.sleep(.005)

    def connected(self,server):
        deadline=time.monotonic()+self.timeout
        while True:
            if self._connect(server,None):return
            error=ctypes.get_last_error()
            if error==535:return
            if error!=536 or time.monotonic()>deadline:raise ctypes.WinError(error)
            time.sleep(.005)

    def send(self,handle,value):
        raw=json.dumps(value,separators=(",",":")).encode()+b"\n"
        contract._require(len(raw)<=16384,"private message exceeds bound")
        count=w.DWORD()
        self.api._ok(self._write(handle,raw,len(raw),ctypes.byref(count),None),"private custody write")
        contract._require(count.value==len(raw),"partial custody write")

    def recv(self,handle):
        deadline=time.monotonic()+self.timeout;raw=self.rx.get(handle,b"")
        while b"\n" not in raw:
            count=w.DWORD()
            self.api._ok(self._peek(handle,None,0,None,ctypes.byref(count),None),"private custody peek")
            if count.value:
                contract._require(len(raw)+count.value<=16384,"private receive exceeds bound")
                buffer=ctypes.create_string_buffer(count.value);read=w.DWORD()
                self.api._ok(self._read(handle,buffer,count.value,ctypes.byref(read),None),"private custody read")
                raw+=buffer.raw[:read.value]
            elif time.monotonic()>deadline:raise TimeoutError("private custody receive timeout")
            else:time.sleep(.005)
        line,tail=raw.split(b"\n",1);self.rx[handle]=tail
        value=json.loads(line)
        contract._require(type(value) is dict,"private object message required")
        return value

    def close(self,handle):
        self.facade.close_owned_handle(handle);self.rx.pop(handle,None)
        holder=self._holders.pop(handle,None)
        if holder is not None and handle in holder._owned:holder._owned.remove(handle)
