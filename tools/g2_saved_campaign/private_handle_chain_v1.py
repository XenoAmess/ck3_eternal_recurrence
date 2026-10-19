"""Default-OFF owned-only four-process custody transport prototype.

This is not a Native issuer or a production receiver. Its only origin is this
process plus two tiny self-created files. No CK3 PID/path/handle is accepted.
CLI numbers locate inherited resources; kernel peer + retained process handles,
an explicit inheritance allowlist and authenticated parent exchange establish
this fixture's chain. No JSON creates an M7 DTO or a production custody holder.
"""
from __future__ import annotations

from contextlib import contextmanager
import ctypes
from ctypes import wintypes as w
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

_REPO = Path(__file__).resolve().parents[2]
_TIMEOUT = 10.0
_ROLES = ("supervisor", "owner", "Queue", "MCPApp")
_SPAWN_LOCK = threading.Lock()
_PROTOTYPE_SEAL = object()


class ChainUnavailable(RuntimeError):
    pass


def _require(ok, reason):
    if not ok:
        raise ChainUnavailable(reason)


def _same_claim(actual, claimed):
    """Claims are only compared with fresh kernel/file observations."""
    _require(type(claimed) is dict and actual == claimed,
             "parent claim differs from inherited kernel resources")


def _ack_rejection(api, handle, message):
    if message.get("kind")=="rejected":
        # Preserve the real refusal before the client closes a nonblocking pipe.
        api.send(handle,{"kind":"rejection_ack"})


class _Windows:
    def __init__(self):
        _require(os.name == "nt", "Windows only")
        sys.path.insert(0, str(_REPO / "ck3_autonomous_player/src"))
        from xar_autoplayer.bridge.native_loaded_provider_windows_v1 import _Win32ReadsV1
        self.reads = _Win32ReadsV1()
        self.k = self.reads.k
        self.owned = set()
        self.rx = {}
        def bind(name, args, result):
            f = getattr(self.k, name); f.argtypes, f.restype = args, result
            return f
        H, D, P = w.HANDLE, w.DWORD, w.LPVOID
        self.event = bind("CreateEventW", [P, w.BOOL, w.BOOL, w.LPCWSTR], H)
        self.set_event = bind("SetEvent", [H], w.BOOL)
        self.flags = bind("GetHandleInformation", [H, ctypes.POINTER(D)], w.BOOL)
        self.set_flags = bind("SetHandleInformation", [H, D, D], w.BOOL)
        self.pipe = bind("CreateNamedPipeW", [w.LPCWSTR,D,D,D,D,D,D,P], H)
        self.connect = bind("ConnectNamedPipe", [H,P], w.BOOL)
        self.peek = bind("PeekNamedPipe", [H,P,D,P,ctypes.POINTER(D),P], w.BOOL)
        self.read = bind("ReadFile", [H,P,D,ctypes.POINTER(D),P], w.BOOL)
        self.write = bind("WriteFile", [H,P,D,ctypes.POINTER(D),P], w.BOOL)
        self.server_pid = bind("GetNamedPipeServerProcessId", [H,ctypes.POINTER(D)], w.BOOL)

    def own(self, handle):
        handle = int(handle)
        _require(handle not in (0, ctypes.c_void_p(-1).value), "invalid owned handle")
        _require(handle not in self.owned, "owned handle collision")
        self.owned.add(handle)
        return handle

    def duplicate(self, handle, *, inherit=False, access=None):
        out = w.HANDLE()
        current = self.reads.current()
        self.reads._ok(self.reads.duplicate(current,handle,current,ctypes.byref(out),
            0 if access is None else access, inherit, 2 if access is None else 0), "owned duplicate")
        return self.own(out.value)

    def inherited(self, handle):
        _require(type(handle) is int and handle > 0, "integer inherited handle required")
        flags = w.DWORD()
        self.reads._ok(self.flags(handle,ctypes.byref(flags)), "inherited handle flags")
        _require(bool(flags.value & 1), "resource was not inherited")
        self.reads._ok(self.set_flags(handle,1,0), "clear inherited flag")
        return self.own(handle)

    def close(self, handle):
        _require(handle in self.owned, "refuse borrowed/unknown close")
        self.reads.close_handle(handle)
        self.owned.remove(handle)
        self.rx.pop(handle, None)

    def cleanup(self):
        errors = []
        for h in tuple(self.owned):
            try: self.close(h)
            except Exception as e: errors.append(type(e).__name__)
        mappings = self.reads.cleanup_temporary_mappings()
        return {"owned_remaining":len(self.owned), "errors":errors,
                "temporary_remaining":mappings["remaining"]}

    def process(self, handle):
        pid,birth,image,alive = self.reads.process_identity(handle)
        _require(alive, "held process is no longer alive")
        return {"pid":pid,"birth_filetime":str(birth),
                "image":os.path.normcase(os.path.abspath(image))}

    def file(self, handle):
        volume,identity,size = self.reads.file_identity(handle)
        name = self.reads.final_path(handle,nt=False)
        digest = self.reads.hash_held_file(handle,size)
        _require(self.reads.file_identity(handle)==(volume,identity,size), "file changed while observed")
        return {"volume":str(volume),"file_id":identity.hex(),"size":size,
                "sha256":digest,"final_path":name}

    def server(self):
        name = r"\\.\pipe\xar_owned_chain_" + secrets.token_hex(20)
        # First local-only, nonblocking instance. Never inherit the server end.
        handle = self.pipe(name,3|0x80000,1|8,1,65536,65536,1000,None)
        return self.own(handle), name

    def client(self, name):
        _require(isinstance(name,str) and name.startswith(r"\\.\pipe\xar_owned_chain_"),
                 "private fixture pipe required")
        deadline = time.monotonic()+_TIMEOUT
        while True:
            handle = self.reads.create(name,0xC0000000,0,None,3,0,None)
            if handle not in (None,0,ctypes.c_void_p(-1).value): return self.own(handle)
            if ctypes.get_last_error() not in (2,231) or time.monotonic()>deadline:
                raise ctypes.WinError(ctypes.get_last_error())
            time.sleep(.01)

    def connected(self, handle):
        deadline = time.monotonic()+_TIMEOUT
        while True:
            if self.connect(handle,None): return
            error = ctypes.get_last_error()
            if error==535: return
            if error!=536 or time.monotonic()>deadline: raise ctypes.WinError(error)
            time.sleep(.01)

    def send(self, handle, message):
        body = json.dumps(message,separators=(",",":")).encode()+b"\n"
        _require(len(body)<=60000, "private frame too large")
        count = w.DWORD()
        self.reads._ok(self.write(handle,body,len(body),ctypes.byref(count),None), "private write")
        _require(count.value==len(body), "partial private write")

    def pending(self, handle):
        count = w.DWORD()
        self.reads._ok(self.peek(handle,None,0,None,ctypes.byref(count),None), "private peek")
        return count.value

    def recv(self, handle, *, timeout=_TIMEOUT):
        deadline = time.monotonic()+timeout
        data = self.rx.get(handle,b"")
        while b"\n" not in data:
            amount = self.pending(handle)
            if amount:
                _require(amount+len(data)<=60000, "private receive extent exceeded")
                buffer = ctypes.create_string_buffer(amount); count = w.DWORD()
                self.reads._ok(self.read(handle,buffer,amount,ctypes.byref(count),None), "private read")
                data += buffer.raw[:count.value]
            elif time.monotonic()>deadline: raise ChainUnavailable("private receive timed out")
            else: time.sleep(.01)
        body,tail = data.split(b"\n",1); self.rx[handle]=tail
        result = json.loads(body)
        _require(type(result) is dict, "private object frame required")
        return result


class _ReceivedFixtureResources:
    """Owned fixture resources, NEVER a Native qualification token."""
    def __init__(self, api, handles, seal):
        _require(seal is _PROTOTYPE_SEAL, "internal fixture receiver required")
        self.api,self.handles,self.valid = api,handles,False
        self.claim = {"target":api.process(handles["target"]),"file":api.file(handles["lease"])}

    def check(self):
        _require(self.valid, "unadopted or revoked fixture resources")
        _require(self.api.reads.wait(self.handles["revoke"],0)==0x102, "root revoked")
        self.api.process(self.handles["parent"])

    def invalidate(self):
        self.valid = False  # A future real owner must clear its M7 DTO/cache here FIRST.
        for h in tuple(self.handles.values()):
            if h in self.api.owned: self.api.close(h)


@contextmanager
def _mcp_single_creation_inheritance(startup, command):
    """Keep installed MCP creator/Job code; scope only its AnyIO call.

    No global AnyIO or subprocess function is patched. The private MCP module
    reference is restored immediately; foreign commands and fallback fail closed.
    The owner must serialize this future one-shot bootstrap before other creates.
    """
    import anyio
    import mcp.os.win32.utilities as utilities
    _require(_SPAWN_LOCK.acquire(blocking=False), "concurrent private MCP bootstrap")
    original = utilities.anyio
    called = [False]
    class Proxy:
        def __getattr__(self, name): return getattr(original,name)
        async def open_process(self, argv, **kwargs):
            _require(not called[0] and list(argv)==command, "foreign/repeated MCP creation")
            called[0]=True
            _require("startupinfo" not in kwargs, "MCP startupinfo collision")
            try:
                return await anyio.open_process(argv,startupinfo=startup,**kwargs)
            except NotImplementedError as error:
                # The installed fallback Popen cannot inherit our resources.
                raise ChainUnavailable("MCP fallback has no custody inheritance") from error
    try:
        utilities.anyio=Proxy()
        yield
        _require(called[0], "actual MCP AnyIO creation was not reached")
    finally:
        utilities.anyio=original
        _SPAWN_LOCK.release()


class _Child:
    def __init__(self, process, handle, *, mcp=None, capture=None, loop=None):
        self.process,self.handle,self.mcp,self.capture,self.loop=process,handle,mcp,capture,loop

    def wait(self):
        if self.mcp is None: return self.process.wait(timeout=_TIMEOUT)
        async def finish():
            import anyio
            with anyio.fail_after(_TIMEOUT): return await self.process.wait()
        return self.loop.run(finish())

    def finish(self):
        code = self.wait()
        if self.mcp is not None:
            # The original creator assigned this exact owned leaf to its Job.
            job=self.mcp._process_jobs.pop(self.process,None)
            if job is not None: self.mcp._close_job_handle(job)
            self.loop.run(self.process.aclose())
            self.loop.run(self.capture.__aexit__(None,None,None))
            self.loop.close()
        else:
            # Popen's process handle belongs to Popen; do not close it via api.
            self.process._handle.Close()
        return code

    def abort_owned_child(self):
        """Only this returned fixture child; never the resource target or Game."""
        if self.mcp is None:
            if self.process.poll() is None: self.process.terminate()
        else:
            self.loop.run(self.mcp.terminate_windows_process_tree(self.process))
        return self.finish()


def _spawn(api, resources, role, *, decoy_handle, use_mcp=False, wrong_parent=False):
    handles={}
    server,name=api.server()
    try:
        for key in ("target","lease","revoke"):
            handles[key]=api.duplicate(resources.handles[key],inherit=True)
        parent_source=resources.handles["target"] if wrong_parent and role=="Queue" else api.reads.current()
        handles["parent"]=api.duplicate(parent_source,inherit=True,access=0x1000|0x100000)
        startup=subprocess.STARTUPINFO(lpAttributeList={"handle_list":list(handles.values())})
        if __package__:
            from .owned_python_launch_v1 import owned_python_launch_v1
        else:
            from owned_python_launch_v1 import owned_python_launch_v1
        executable,env=owned_python_launch_v1()
        command=[executable,"-B","-X","utf8",str(Path(__file__).resolve()),
                 "--internal-owned-child",role,json.dumps({"handles":handles,"pipe":name,
                 "decoy":decoy_handle,"wrong_parent":wrong_parent},separators=(",",":"))]
        if not use_mcp:
            process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,startupinfo=startup,close_fds=True,
                creationflags=subprocess.CREATE_NO_WINDOW,env=env)
            child=_Child(process,int(process._handle))
        else:
            import asyncio
            import mcp.client.stdio as stdio
            import mcp.os.win32.utilities as utilities
            from sdk_process_custody import retain_mcp_stdio_process
            loop=asyncio.new_event_loop()
            capture=retain_mcp_stdio_process(stdio,expected_executable=executable)
            async def create():
                observed=await capture.__aenter__()
                with _mcp_single_creation_inheritance(startup,command):
                    process=await stdio._create_platform_compatible_process(command[0],command[1:],env=env)
                generation=observed.generation
                _require(generation is not None,"MCP actual child handle was not retained")
                return process,generation._handle
            try: process,handle=loop.run_until_complete(create())
            except BaseException:
                loop.run_until_complete(capture.__aexit__(*sys.exc_info()));loop.close();raise
            # run() is a uniform synchronous adapter for this private event loop.
            loop.run=loop.run_until_complete
            child=_Child(process,int(handle),mcp=utilities,capture=capture,loop=loop)
        # Sender copies remain until kernel-bound receiver ACK below.
        return child,server,handles
    except BaseException:
        for handle in tuple(handles.values()):
            if handle in api.owned: api.close(handle)
        if server in api.owned: api.close(server)
        raise


def _parent_accept(api, child, server, sender, resources, *, wrong_claim=False):
    api.connected(server)
    peer=api.reads.pipe_client_pid(server)
    child_identity=api.process(child.handle)
    _require(peer==child_identity["pid"]==child.process.pid,"actual returned child/pipe peer differs")
    hello=api.recv(server)
    _ack_rejection(api,server,hello)
    _require(hello.get("kind")=="hello","receiver rejected kernel peer: "+str(hello.get("reason")))
    _same_claim(child_identity,hello.get("self"))
    _same_claim(resources.claim,hello.get("resources"))
    claim=json.loads(json.dumps(resources.claim))
    if wrong_claim: claim["file"]["sha256"]="0"*64
    api.send(server,{"kind":"accept","resources":claim})
    ack=api.recv(server)
    _ack_rejection(api,server,ack)
    _require(ack.get("kind")=="adopted","receiver did not adopt: "+str(ack.get("reason")))
    # The actual inherited receiver now owns matching held resources.
    for handle in sender.values(): api.close(handle)
    return child_identity


def _child_main(role, hints):
    api=_Windows(); resources=None; child=None; server=None; upstream=None
    receipt={"role":role,"source_fixture":True,"Native_DTO_issued":False}
    try:
        _require(role in _ROLES[1:],"invalid fixture role")
        _require(type(hints) is dict and set(hints)=={"handles","pipe","decoy","wrong_parent"}
                 and type(hints["wrong_parent"]) is bool,"malformed location hints")
        supplied=hints["handles"]
        _require(type(supplied) is dict and set(supplied)=={"target","lease","revoke","parent"},"missing inherited resource")
        handles={k:api.inherited(v) for k,v in supplied.items()}
        resources=_ReceivedFixtureResources(api,handles,_PROTOTYPE_SEAL)
        parent=api.process(handles["parent"])
        upstream=api.client(hints["pipe"])
        server_pid=w.DWORD()
        api.reads._ok(api.server_pid(upstream,ctypes.byref(server_pid)),"actual parent pipe PID")
        _require(server_pid.value==parent["pid"],"server is not held parent")
        own=api.process(api.reads.current())
        # A decoy handle number never authorizes a resource; compare FileID only.
        decoy_hint=hints["decoy"]
        _require(type(decoy_hint) is dict and set(decoy_hint)=={"handle","file_id"},"invalid excluded decoy hint")
        try: decoy=api.reads.file_identity(decoy_hint["handle"])
        except (OSError,ValueError): decoy=None
        _require(decoy is None or decoy[1].hex()!=decoy_hint["file_id"],"excluded decoy was inherited")
        ctypes.set_last_error(0)
        _require(not api.set_event(handles["revoke"]) and ctypes.get_last_error()==5,
                 "receiver must not possess revocation-event modify rights")
        api.send(upstream,{"kind":"hello","self":own,"resources":resources.claim})
        accepted=api.recv(upstream)
        _require(accepted.get("kind")=="accept","missing parent acceptance")
        _same_claim(resources.claim,accepted.get("resources"))
        resources.valid=True
        api.send(upstream,{"kind":"adopted"})
        receipt.update(process=own,parent=parent,pipe_server_pid=server_pid.value,
                       exact_resources=resources.claim,adopted=True,decoy_not_used=True)
        following=_ROLES.index(role)+1
        descendants=[]
        if following<len(_ROLES):
            child,server,sender=_spawn(api,resources,_ROLES[following],decoy_handle=hints["decoy"],
                use_mcp=following==3,wrong_parent=hints["wrong_parent"])
            _parent_accept(api,child,server,sender,resources)
            ready=api.recv(server)
            _ack_rejection(api,server,ready)
            _require(ready.get("kind")=="chain_ready","child chain not ready: "+str(ready.get("reason")))
            descendants=ready["nodes"]
        api.send(upstream,{"kind":"chain_ready","nodes":[receipt,*descendants]})
        cause=None
        while cause is None:
            try:
                resources.check()
                if api.rx.get(upstream) or api.pending(upstream):
                    message=api.recv(upstream)
                    _require(message.get("kind")=="revoke","unexpected authenticated parent command")
                    cause="parent_revoke"
            except (ChainUnavailable,OSError) as error: cause=str(error)
            if cause is None: time.sleep(.01)
        resources.valid=False
        children=[]
        if child is not None:
            # A shared-root revocation reaches every hop independently. Do not
            # write to an already-closing child after it reported revocation.
            if api.reads.wait(handles["revoke"],0)==0x102:
                api.send(server,{"kind":"revoke"})
            closed=api.recv(server)
            _ack_rejection(api,server,closed)
            _require(closed.get("kind")=="revoked","child did not revoke: "+str(closed.get("reason")))
            children=closed["nodes"]
            _require(child.finish()==0,"owned child did not exit normally")
            child=None
        resources.invalidate()
        if server is not None: api.close(server);server=None
        receipt.update(valid_before_close=False,revocation_cause=cause,
                       resource_handles_remaining=sum(h in api.owned for h in handles.values()))
        api.send(upstream,{"kind":"revoked","nodes":[receipt,*children]})
        api.close(upstream);upstream=None
        cleanup=api.cleanup()
        _require(cleanup=={"owned_remaining":0,"errors":[],"temporary_remaining":0},
                 "receiver cleanup unverified")
        return 0
    except BaseException as error:
        if resources is not None: resources.valid=False
        if child is not None:
            try: child.abort_owned_child()
            except Exception: pass
        if upstream is not None:
            try:
                api.send(upstream,{"kind":"rejected","reason":type(error).__name__+":"+str(error)})
                api.recv(upstream,timeout=2)
            except Exception: pass
        return 2
    finally:
        api.cleanup()


def run_owned_fixture_v1(*, enabled=False, wrong_claim=False, wrong_parent=False, workspace=None):
    """Opt-in mechanical fixture, self process + tiny files ONLY; never issues H."""
    if enabled is not True:
        return {"status":"default_off","Native_DTO_issued":False,"H":"unknown"}
    api=_Windows(); child=None; directory=None; resources=None
    result={"source_fixture":True,"Native_DTO_issued":False,"H":"unknown",
            "current_Game_access":0,"new_DLLs":0,"roles":list(_ROLES)}
    try:
        root=Path(workspace or (_REPO/"_runtime")).resolve()
        _require(root==(_REPO/"_runtime").resolve(),"fixture root must be project _runtime")
        root.mkdir(exist_ok=True)
        directory=tempfile.TemporaryDirectory(prefix="owned-private-chain-",dir=root)
        file=Path(directory.name)/"owned-lease.txt";file.write_bytes(b"owned private chain fixture only\n")
        decoy=Path(directory.name)/"owned-decoy.txt";decoy.write_bytes(b"decoy\n")
        lease=api.own(api.reads.open_read_shared_file(str(file)))
        decoy_handle=api.own(api.reads.open_read_shared_file(str(decoy)))
        api.reads._ok(api.set_flags(decoy_handle,1,1),"make excluded decoy inheritable")
        target=api.own(api.reads.duplicate_target_read_handle(api.reads.current()))
        event=api.own(api.event(None,True,False,None))
        sync=api.duplicate(event,access=0x100000)
        handles={"target":target,"lease":lease,"revoke":sync}
        resources=object.__new__(_ReceivedFixtureResources)
        resources.api,resources.handles,resources.valid=api,handles,True
        resources.claim={"target":api.process(target),"file":api.file(lease)}
        _require(resources.claim["target"]["pid"]==os.getpid(),"fixture target must be this process")
        decoy_hint={"handle":decoy_handle,"file_id":api.reads.file_identity(decoy_handle)[1].hex()}
        child,server,sender=_spawn(api,resources,"owner",decoy_handle=decoy_hint,wrong_parent=wrong_parent)
        try: _parent_accept(api,child,server,sender,resources,wrong_claim=wrong_claim)
        except ChainUnavailable as error:
            _require(wrong_claim,"unexpected chain refusal: "+str(error))
            _require(child.finish()==2,"wrong claim child did not reject normally")
            child=None;result.update(status="wrong_claim_rejected",reason=str(error));return result
        _require(not wrong_claim,"wrong claim unexpectedly accepted")
        ready=api.recv(server)
        _ack_rejection(api,server,ready)
        if wrong_parent:
            _require(ready.get("kind")=="rejected" and "server is not held parent" in str(ready.get("reason")),
                     "wrong parent did not fail at kernel peer binding: "+str(ready))
            _require(child.finish()==2,"wrong parent chain did not reject normally")
            child=None;result.update(status="wrong_parent_peer_rejected",reason=ready["reason"]);return result
        _require(ready.get("kind")=="chain_ready","four-role chain not ready: "+str(ready.get("reason")))
        _require([n["role"] for n in ready["nodes"]]==list(_ROLES[1:]),"wrong process chain")
        api.reads._ok(api.set_event(event),"root revoke owned event")
        revoked=api.recv(server)
        _require(revoked.get("kind")=="revoked","chain did not revoke: "+str(revoked.get("reason")))
        nodes=revoked["nodes"]
        _require(all(n.get("valid_before_close") is False and n.get("resource_handles_remaining")==0 for n in nodes),
                 "receiver release or revocation unproved")
        _require(child.finish()==0,"owner did not exit normally");child=None
        result.update(status="owned_chain_pass",nodes=nodes,root=resources.claim,
                      actual_MCP_creator=True,revocation="root readonly-shared event; parent peer also checked")
        return result
    finally:
        if resources is not None: resources.valid=False
        if child is not None:
            try: result["abort_child_exit"]=child.abort_owned_child()
            except Exception as e: result["abort_error"]=type(e).__name__
        result["cleanup"]=api.cleanup()
        if directory is not None:
            directory.cleanup()
        result["fixture_directory_removed"]=directory is None or not Path(directory.name).exists()


if __name__=="__main__":
    if len(sys.argv)==4 and sys.argv[1]=="--internal-owned-child":
        raise SystemExit(_child_main(sys.argv[2],json.loads(sys.argv[3])))
    raise SystemExit("Internal opt-in fixture only; import run_owned_fixture_v1. No production CLI.")
