"""Default-OFF pure creator/receiver adapters, never a deployed cold launcher.

Only actual Popen/MCP creator returns establish an edge. Private message handle
numbers are locations; all authoritative observations come from held resources.
No function opens a PID from JSON, alters a Game/Job, or restarts an attempt.
"""
from contextlib import asynccontextmanager
import hashlib
import json
from pathlib import Path
import subprocess

from xar_autoplayer.bridge import native_loaded_provider_custody_v1 as contract
from xar_autoplayer.bridge.native_loaded_provider_origin_io_v1 import OriginKernelIOV1
from xar_autoplayer.bridge.native_loaded_provider_origin_v1 import (
    _epoch,_record_actual_child_v1,_pull_actual_chain_v1,
    prepare_canonical_origin_v1)
from xar_autoplayer.bridge.native_loaded_provider_receiver_v1 import (
    receive_inherited_preload_v1,bind_received_owner_v1)


def consume_private_bootstrap_args_v1(argv,*,enabled=False):
    """Outer owned entry only; strip locations before its original CLI parser."""
    contract._require(type(argv) is list and all(isinstance(v,str) for v in argv),"actual argv required")
    marker="--xar-private-preload"
    if enabled is not True:return list(argv),None
    if marker not in argv:return list(argv),None
    contract._require(len(argv)>=3 and argv.count(marker)==1 and argv[-2]==marker and len(argv[-1].encode())<=16384,
                      "one bounded private bootstrap suffix required")
    hints=json.loads(argv[-1])
    contract._require(type(hints) is dict,"private bootstrap locations must be an object")
    return list(argv[:-2]),hints


def _verified_entry_sources(pins):
    contract._require(isinstance(pins,(tuple,list)) and 0<len(pins)<=8,"frozen entry source pins required")
    result=[]
    for row in pins:
        contract._require(isinstance(row,(tuple,list)) and len(row)==2 and isinstance(row[0],str)
            and Path(row[0]).is_absolute() and contract._sha(row[1]),"exact entry path/SHA required")
        path=Path(row[0]).resolve(strict=True)
        with path.open("rb") as stream:raw=stream.read(1048577)
        contract._require(len(raw)<=1048576 and hashlib.sha256(raw).hexdigest()==row[1],"frozen entry source changed")
        result.append((str(path),row[1]))
    contract._require(len({row[0] for row in result})==len(result),"duplicate entry source")
    return tuple(sorted(result))


def _creator_digest(entries):
    root=Path(__file__).resolve().parent
    files=(Path(__file__).resolve(),root/"mcp_owned_stdio_binding_v1.py",root/"sdk_process_custody.py")
    return hashlib.sha256(json.dumps(([(p.name,hashlib.sha256(p.read_bytes()).hexdigest()) for p in files],entries),
        separators=(",",":")).encode()).hexdigest()


def _require_direct_entry_command_v1(command, entry):
    """Finite Python script form; an entry appearing in argv is insufficient."""
    contract._require(type(command) is list and len(command)>=2
        and all(isinstance(arg,str) for arg in command)
        and Path(command[0]).is_absolute(),"exact direct Python script command required")
    index=1;seen=set()
    while index<len(command) and command[index].startswith("-"):
        flag=command[index]
        contract._require(flag in ("-B","-u","-X") and flag not in seen,
                          "unsupported Python interpreter flag or execution mode")
        seen.add(flag);index+=1
        if flag=="-X":
            contract._require(index<len(command) and command[index]=="utf8",
                              "only the frozen Python utf8 interpreter option is supported")
            index+=1
    contract._require(index<len(command) and Path(command[index]).is_absolute()
        and str(Path(command[index]).resolve(strict=True))==entry,
        "actual Python script operand is not the frozen entry")
    return index


def _require_returned_image_v1(actual, expected):
    # Reuse the retained MCP creator's exact image-path semantics. The held
    # returned process is observed directly; a launcher descendant is not used.
    from g2_saved_campaign.sdk_process_custody import _executable_path, _path_identity
    actual=contract._process(actual)
    contract._require(_path_identity(_executable_path(actual.executable))
        ==_path_identity(_executable_path(expected)),
        "actual returned child executable differs from the direct command image")


class CanonicalPreloadFactoryV1:
    """Keep original/unknown resources strongly even if runtime.launch fails."""
    def __init__(self,*,facade,machine_id,expected_dll_sha256,entry_source_pins=(),enabled=False):
        self.facade,self.machine_id,self.expected_sha=facade,machine_id,expected_dll_sha256
        self.enabled=enabled is True;self.holder=self.origin=None;self.attempted=False
        self.entry_source_pins=entry_source_pins

    def pre_native_resume(self,process,config):
        if not self.enabled:return None
        contract._require(not self.attempted,"canonical preload callback is once-only")
        self.attempted=True
        entries=_verified_entry_sources(self.entry_source_pins)
        self.holder=contract.prepare_canonical_cold_custody_v1(target=process,dll_path=str(config.dll_path),
            expected_dll_sha256=self.expected_sha,machine_id=self.machine_id,pipe_name=config.pipe_name,
            os_facade=self.facade,enabled=True)
        contract._require(self.holder is not None and not self.holder.closed,"canonical preload unavailable: "+
            str(getattr(self.facade,"_preload_prepare_error_v1","unknown")))
        self.holder._entry_source_pins_v1=entries
        self.holder._creator_source_digest_v1=_creator_digest(entries)
        self.origin=prepare_canonical_origin_v1(custody=self.holder,enabled=True)
        return self.holder

    def close(self):
        return self.holder.close() if self.holder is not None else None


class _ChildPlanV1:
    def __init__(self,holder,role,command,env,cwd,entry_source):
        self.holder,self.role,self.cwd=holder,role,str(Path(cwd).resolve())
        self.io=getattr(holder,"_canonical_chain_io_v1",None)
        contract._require(type(self.io) is OriginKernelIOV1 and self.io.facade is holder.facade,
                          "same local canonical chain transport required")
        entries=_verified_entry_sources(holder._entry_source_pins_v1)
        contract._require(holder._creator_source_digest_v1==_creator_digest(entries),"actual creator source changed")
        contract._require(type(command) is list and command and all(isinstance(v,str) for v in command)
            and Path(command[0]).is_absolute() and type(env) is dict,"exact command/environment required")
        entry=str(Path(entry_source).resolve(strict=True))
        contract._require(entry in {p for p,_sha in entries},
            "actual command entry is outside frozen source closure")
        _require_direct_entry_command_v1(command,entry)
        expected={"supervisor":"owner","owner":"Queue","Queue":"MCPApp"}
        parent_role=getattr(holder,"_creation_role_v1",None)
        contract._require(expected.get(parent_role)==role and not getattr(holder,"_creation_attempted_v1",False),
                          "one ordered canonical creation edge required")
        holder._creation_attempted_v1=True
        self.child=self.edge=None;self.started=False;self.error=None;self.sender=[]
        origin=getattr(holder,"_canonical_origin_v1",None)
        if origin is not None:
            origin_handle,origin_pipe,revoke=origin.origin_handle,origin.pipe_name,origin.revoke_handle
        else:
            origin_handle,origin_pipe=holder._origin_process_handle_v1,holder._origin_pipe_name_v1
            revoke=holder.facade._received_preloads_v1[holder].revoke_handle
        self.server,name=self.io.server(holder=holder)
        locations={}
        for key,value,access in (("target",holder.process_handle,self.io.api.PROCESS_READ_ACCESS),
                ("lease",holder.dll_handle,None),("revoke",revoke,0x100000),
                ("parent",self.io.api.current(),self.io.api.PROCESS_READ_ACCESS),
                ("origin",origin_handle,self.io.api.PROCESS_READ_ACCESS)):
            locations[key]=self.io.duplicate(value,holder=holder,inherit=True,access=access)
            self.sender.append(locations[key])
        hints={"role":role,"locations":locations,"control_pipe":name,"origin_pipe":origin_pipe,
               "machine_id":holder.machine_id,"native_pipe_name":holder.pipe_name,"entry_sources":entries}
        self.command=tuple(command+["--xar-private-preload",json.dumps(hints,separators=(",",":"))])
        self.env=dict(env)
        self.startup=subprocess.STARTUPINFO(lpAttributeList={"handle_list":list(self.sender)})

    def acknowledge(self,child,handle):
        _require_returned_image_v1(self.io.facade.observe_process(handle),self.command[0])
        self.edge=_record_actual_child_v1(self.holder,self.io,child,handle,self.server,self.role)
        for handle in tuple(self.sender):self.io.close(handle);self.sender.remove(handle)
        return self.edge


def prepare_child_v1(holder,*,role,command,env,cwd,entry_source=None,enabled=False):
    if enabled is not True:return None
    contract._require(type(holder) is contract._PreloadCustodyV1 and holder.seal is contract._RESOURCE_SEAL
        and not holder.closed,"same original custody resource required")
    return _ChildPlanV1(holder,role,command,env,cwd,entry_source)


def spawn_owned_popen_v1(plan,*,stdout=None,stderr=None,after_process_create=None):
    """Exact single call; original Popen remains process cleanup owner."""
    contract._require(type(plan) is _ChildPlanV1 and not plan.started,"one actual child creation required")
    plan.started=True
    try:
        plan.child=subprocess.Popen(list(plan.command),env=plan.env,cwd=plan.cwd,
            startupinfo=plan.startup,close_fds=True,stdin=subprocess.DEVNULL,
            stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
        if after_process_create is not None:after_process_create(plan.child)
        return plan.acknowledge(plan.child,int(plan.child._handle))
    except BaseException as error:
        plan.error=error  # exact child/handles retained; no hidden retry
        raise


@asynccontextmanager
async def spawn_owned_mcp_v1(plan,*,errlog=None):
    """Keep original stock MCP Job/stdio cleanup, per-session globals only."""
    contract._require(type(plan) is _ChildPlanV1 and plan.role=="MCPApp" and not plan.started,
                      "one exact MCP App creation required")
    plan.started=True
    import mcp.client.stdio as stock
    from g2_saved_campaign.mcp_owned_stdio_binding_v1 import bind_owned_stdio_v1
    from g2_saved_campaign.sdk_process_custody import retain_mcp_stdio_process
    params=stock.StdioServerParameters(command=plan.command[0],args=list(plan.command[1:]),
                                      env=plan.env,cwd=plan.cwd)
    binding=bind_owned_stdio_v1(inherited_custody=plan.holder,expected_server=params,
                              startupinfo=plan.startup,enabled=True)
    plan.binding=binding
    try:
        async with retain_mcp_stdio_process(binding.private_stdio,expected_executable=plan.command[0]) as capture:
            async with binding.stdio_client(params,errlog=errlog) as streams:
                plan.child=binding.created_child
                generation=capture.require_generation()
                edge=plan.acknowledge(plan.child,generation._handle)
                yield edge,streams,generation
    except BaseException as error:
        plan.error=error
        raise


def receive_child_bootstrap_v1(hints,*,facade,enabled=False):
    if enabled is not True:return None
    contract._require(type(hints) is dict and set(hints)=={"role","locations","control_pipe","origin_pipe",
        "machine_id","native_pipe_name","entry_sources"} and hints["role"] in ("owner","Queue","MCPApp"),
        "private bootstrap locations required")
    locations=hints["locations"]
    contract._require(type(locations) is dict and set(locations)=={"target","lease","parent","revoke","origin"}
        and all(type(v) is int and v>0 for v in locations.values()) and len(set(locations.values()))==5,
        "five distinct inherited resource locations required")
    io=OriginKernelIOV1(facade,enabled=True)
    control=io.client(hints["control_pipe"])
    result=receive_inherited_preload_v1(inherited={k:v for k,v in locations.items() if k!="origin"},
        owned_control_handle=control,facade=facade,machine_id=hints["machine_id"],
        native_pipe_name=hints["native_pipe_name"],enabled=True,_control_transfer_seal=contract._RESOURCE_SEAL)
    contract._require(result.available,result.reason)
    holder=result.holder
    try:
        io.adopt_inherited(locations["origin"],holder=holder)
        original=contract._process(facade.observe_process(locations["origin"]))
        if hints["role"]=="owner":
            contract._require(contract._same_process(original,facade.observe_process(locations["parent"])),
                              "first parent is not held canonical origin")
        holder._origin_process_handle_v1=locations["origin"]
        holder._origin_pipe_name_v1=hints["origin_pipe"]
        holder._creation_role_v1=hints["role"]
        holder._canonical_chain_io_v1=io
        holder._entry_source_pins_v1=_verified_entry_sources(hints["entry_sources"])
        holder._creator_source_digest_v1=_creator_digest(holder._entry_source_pins_v1)
        io.send(control,{"kind":"staged","role":hints["role"],"epoch":_epoch(),"creator":holder._creator_source_digest_v1})
        contract._require(io.recv(control)=={"kind":"parent_accepted","epoch":_epoch(),
            "creator":holder._creator_source_digest_v1},
                          "parent source epoch/bootstrap differs")
        return result,io,control
    except Exception:
        holder.close()
        raise


def export_actual_child_chain_v1(result,io,control,edge=None):
    handles=() if edge is None else _pull_actual_chain_v1(edge)
    roles={"owner":("Queue","MCPApp"),"Queue":("MCPApp",),"MCPApp":()}[result.holder._creation_role_v1]
    contract._require(len(roles)==len(handles),"actual export chain incomplete")
    io.send(control,{"kind":"actual_child_exports","exports":[{"role":r,"location":h} for r,h in zip(roles,handles)]})
    return handles


def install_received_provider_bootstrap_v1(service,result,*,enabled=False):
    """After the original App factory retained its one actual Service."""
    if enabled is not True:return None
    owner=getattr(service,"_successor_ui_app_owner_v1",None)
    contract._require(owner is not None and owner.service is service,"original installed App owner required")
    bind_received_owner_v1(result,owner)
    holder=result.holder
    # origin handle has already been locally adopted by the earlier receiver.
    from xar_autoplayer.bridge.native_loaded_provider_origin_v1 import _OriginSessionV1
    io=OriginKernelIOV1(holder.facade,enabled=True)
    session=_OriginSessionV1(holder,io,holder._origin_process_handle_v1,holder._origin_pipe_name_v1)
    holder._origin_session_v1=session
    return owner
