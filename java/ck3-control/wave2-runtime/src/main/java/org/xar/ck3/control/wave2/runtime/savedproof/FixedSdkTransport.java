package org.xar.ck3.control.wave2.runtime.savedproof;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.recovery.RecoveryEvidence;

/** Fixed transport into an existing SDK function. No action, recovery or admission policy. */
public final class FixedSdkTransport {
    private FixedSdkTransport() { }

    public static String sourceSha256() { return RecoveryEvidence.sha256(PROGRAM.getBytes(StandardCharsets.UTF_8)); }

    public static byte[] request(SavedProofReadTicket ticket) {
        return request(ticket,false);
    }
    static byte[] request(SavedProofReadTicket ticket, boolean coldRestore) {
        return request(ticket,coldRestore,null);
    }
    static byte[] request(SavedProofReadTicket ticket, boolean coldRestore, ExactRef inventoryRef) {
        ObjectNode value = StrictJson.object();
        value.put("schema", "xar.fixed-original-sdk-measurement-request/v1");
        if (coldRestore) { value.put("schema","xar.fixed-original-sdk-measurement-request/v2"); value.put("purpose","POST_HELLO_COLD_RESTORE"); }
        if (inventoryRef != null) {
            value.put("schema","xar.fixed-original-sdk-measurement-request/v3");
            value.put("purpose",coldRestore?"POST_HELLO_COLD_RESTORE":"CLOSED_CHECKPOINT");
            value.set("source_inventory_ref",inventoryRef.toJson());
        }
        value.put("machine_id", ticket.machineId()); value.put("nonce", ticket.nonce());
        value.put("review_at_utc", ticket.reviewAt().toString());
        value.put("driver_path", ticket.driverPath().toString()); value.set("driver_identity", ticket.driverIdentity().toJson());
        value.set("save_ref", ticket.save().toJson()); value.set("save_identity", ticket.saveIdentity().toJson());
        value.put("sdk_root", ticket.sdkRoot().toString()); value.set("sdk_freeze_ref", ticket.sdkFreeze().toJson());
        value.set("validator_ref", ticket.validatorSource().toJson()); value.put("pipe_name", ticket.pipeName());
        value.put("max_driver_bytes", ticket.maxDriverBytes()); value.put("worker_source_sha256", sourceSha256());
        return StrictJson.canonical(value);
    }
    static byte[] sourceInventory(SavedProofReadTicket ticket, Map<String,ExactRef> pins) {
        var value=StrictJson.object();value.put("schema","xar.java-verified-sdk-source-inventory/v1");
        value.put("machine_id",ticket.machineId());value.put("sdk_root",ticket.sdkRoot().toString());
        value.set("sdk_freeze_ref",ticket.sdkFreeze().toJson());var files=value.putArray("files");
        StrictJson.require(!pins.isEmpty() && pins.size()<=4096,"complete bounded Java-verified source inventory");
        pins.entrySet().stream().sorted(Map.Entry.comparingByKey()).forEach(entry->{
            var row=StrictJson.object();row.put("relative",entry.getKey());row.set("source_ref",entry.getValue().toJson());files.add(row);
        });
        return StrictJson.canonical(value,1_048_576);
    }

    /* File protection/measurement plumbing only. The imported validator is never replaced.
       The SDK is the sole SAVE-body reader; profile events count its actual hash calls. */
    public static final String PROGRAM = """
import ctypes,hashlib,importlib.abc,importlib.machinery,json,msvcrt,os,sys,types
from ctypes import wintypes
from datetime import datetime,timezone
from pathlib import Path

counts={'driver_physical_body_reads':0,'driver_physical_read_bytes':0,'original_validator_calls':0,'save_sha256_calls':0}
handles=[]
def require(ok,message):
    if not ok: raise ValueError(message)
def unique_object(pairs):
    result={}
    for key,value in pairs:
        require(key not in result,'duplicate JSON object field')
        result[key]=value
    return result
def decode(raw):
    return json.loads(raw,object_pairs_hook=unique_object)
def bounded(path,limit):
    p=Path(path)
    require(p.is_absolute() and p.is_file() and p.stat().st_size<=limit,'finite existing source metadata')
    with p.open('rb') as s: raw=s.read(limit+1)
    require(len(raw)<=limit,'source metadata cap')
    return raw
def exact(ref,limit):
    require(type(ref) is dict and set(ref)=={'path','bytes','sha256'},'exact source ref')
    require(type(ref['bytes']) is int and 0<=ref['bytes']<=limit,'source-specific finite bytes')
    raw=bounded(ref['path'],limit)
    require(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'exact source bytes')
    return raw
def identity(path):
    p=Path(path);s=os.stat(p,follow_symlinks=False)
    require(not s.st_file_attributes & 0x400,'ordinary non-reparse file')
    return {'bytes':s.st_size,'file_id':str(s.st_ino),'mtime_ns':str(s.st_mtime_ns)}
def emit(value):
    raw=json.dumps(value,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')
    require(len(raw)<=65536,'small SDK transport output')
    sys.stdout.buffer.write(raw+b'\\n');sys.stdout.buffer.flush()
try:
    require(os.name=='nt' and len(sys.argv)==2,'fixed Windows SDK transport')
    request=decode(bounded(sys.argv[1],65536))
    delegated=request.get('schema')=='xar.fixed-original-sdk-measurement-request/v3'
    cold_restore=request.get('purpose')=='POST_HELLO_COLD_RESTORE'
    fields={'schema','machine_id','nonce','review_at_utc','driver_path','driver_identity','save_ref','save_identity','sdk_root','sdk_freeze_ref','validator_ref','pipe_name','max_driver_bytes','worker_source_sha256'}
    require(set(request)==(fields|{'purpose','source_inventory_ref'} if delegated else fields|{'purpose'} if cold_restore else fields),'fixed request fields')
    require((delegated and request['purpose'] in ('POST_HELLO_COLD_RESTORE','CLOSED_CHECKPOINT')) or (cold_restore and request['schema']=='xar.fixed-original-sdk-measurement-request/v2') or request['schema']=='xar.fixed-original-sdk-measurement-request/v1','fixed request schema')
    deadline=datetime.fromisoformat(request['review_at_utc'].replace('Z','+00:00'))
    def require_live():
        require(datetime.now(timezone.utc)<deadline,'read release expired before new body operation')
    require_live()
    root=Path(request['sdk_root']).resolve(strict=True)
    freeze=decode(exact(request['sdk_freeze_ref'],1048576))
    if delegated:
        inventory=decode(exact(request['source_inventory_ref'],1048576))
        require(type(inventory) is dict and set(inventory)=={'schema','machine_id','sdk_root','sdk_freeze_ref','files'},'exact Java source inventory transport')
        require(inventory['schema']=='xar.java-verified-sdk-source-inventory/v1' and inventory['machine_id']==request['machine_id'] and Path(inventory['sdk_root']).resolve(strict=True)==root and inventory['sdk_freeze_ref']==request['sdk_freeze_ref'],'same Java-verified SDK source scope')
        rows=inventory['files'];require(type(rows) is list and 0<len(rows)<=4096,'bounded complete source transport')
    else:
        require(freeze['machine_id']==request['machine_id'] and Path(freeze['source_root']).resolve(strict=True)==root,'actual SDK source root/machine')
        rows=freeze['files']
    pins={}
    for row in rows:
        require(type(row) is dict and (not delegated or set(row)=={'relative','source_ref'}),'typed Java source item')
        name=row['relative'];require(type(name) is str and name not in pins,'unique SDK source item')
        require(not Path(name).is_absolute() and '..' not in Path(name).parts,'SDK source child')
        source_cap=2097152 if Path(name).suffix.lower() in ('.py','.pyi') else 8388608
        source=row['source_ref'] if delegated else {'path':str(root/name),'bytes':row['bytes'],'sha256':row['sha256']}
        require(type(source) is dict and set(source)=={'path','bytes','sha256'} and Path(source['path']).resolve(strict=True)==root/name,'exact confined source transport')
        require(type(source['bytes']) is int and 0<=source['bytes']<=source_cap,'explicit SDK source cap')
        pins[name]=source
    require(not any(n=='xar_autoplayer' or n.startswith('xar_autoplayer.') for n in sys.modules),'fresh frozen SDK namespace')
    class FrozenLoader(importlib.machinery.SourceFileLoader):
        def get_code(self,fullname):
            p=Path(self.path).resolve(strict=True)
            require(p.is_relative_to(root),'frozen import child')
            relative=p.relative_to(root).as_posix();require(relative in pins,'frozen import inventory authority')
            return compile(exact(pins[relative],2097152),str(p),'exec',dont_inherit=True)
    class FrozenFinder(importlib.abc.MetaPathFinder):
        def find_spec(self,fullname,path=None,target=None):
            if fullname!='xar_autoplayer' and not fullname.startswith('xar_autoplayer.'): return None
            spec=importlib.machinery.PathFinder.find_spec(fullname,path,target)
            require(spec is not None and spec.origin is not None and spec.origin.endswith('.py'),'pinned Python SDK source import')
            spec.loader=FrozenLoader(fullname,spec.origin)
            return spec
    sys.dont_write_bytecode=True;sys.path.insert(0,str(root));sys.meta_path.insert(0,FrozenFinder())
    from xar_autoplayer.cold_checkpoint_validator import validate_cold_start_checkpoint_payload_for_pipe as validator
    from xar_autoplayer import native_session
    require(Path(validator.__code__.co_filename).resolve()==Path(request['validator_ref']['path']).resolve(),'actual validator code origin')
    exact(request['validator_ref'],65536)
    imports=[]
    def check_imports():
        imports.clear()
        for name,module in tuple(sys.modules.items()):
            if name=='xar_autoplayer' or name.startswith('xar_autoplayer.'):
                filename=getattr(module,'__file__',None)
                if filename is None: continue
                p=Path(filename).resolve(strict=True)
                require(p.is_relative_to(root),'all loaded SDK dependencies frozen')
                relative=p.relative_to(root).as_posix();require(relative in pins,'imported source listed in SDK manifest')
                cached=getattr(module,'__cached__',None)
                require(cached is None or not Path(cached).exists(),'unqualified bytecode cache rejected')
                raw=exact(pins[relative],2097152)
                imports.append({'relative':relative,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    check_imports()
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE]
    k.CreateFileW.restype=wintypes.HANDLE;k.CloseHandle.argtypes=[wintypes.HANDLE]
    def protected(path):
        require_live()
        h=k.CreateFileW(str(path),0x80000080,1,None,3,0x00200000,None)
        if h==ctypes.c_void_p(-1).value: raise ctypes.WinError(ctypes.get_last_error())
        handles.append(h);return h
    driver=Path(request['driver_path']);save=Path(request['save_ref']['path'])
    dh=protected(driver);protected(save)
    before_driver=identity(driver);before_save=identity(save)
    require(before_driver==request['driver_identity'] and before_save==request['save_identity'],'current protected file identities')
    cap=request['max_driver_bytes'];require(type(cap) is int and 0<before_driver['bytes']<=cap<=67108864,'whole Driver within granted bytes')
    fd=msvcrt.open_osfhandle(dh,os.O_RDONLY|os.O_BINARY);handles.remove(dh)
    with os.fdopen(fd,'rb') as stream:
        require_live()
        counts['driver_physical_body_reads']+=1;counts['driver_physical_read_bytes']=None
        raw=stream.read(cap);counts['driver_physical_read_bytes']=len(raw)
        require(len(raw)==before_driver['bytes'],'whole stable Driver payload')
        driver_ref={'path':str(driver),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
        payload=decode(raw)
        hash_function=native_session._sha256_file
        def profile(frame,event,arg):
            if event=='call':
                if frame.f_code is validator.__code__:
                    require_live();counts['original_validator_calls']+=1
                if frame.f_code is hash_function.__code__:
                    require_live();counts['save_sha256_calls']+=1
        sys.setprofile(profile)
        try: anchor=validator(types.SimpleNamespace(profile_dir=save.parent.parent),request['pipe_name'],payload)
        finally: sys.setprofile(None)
        after_driver=identity(driver);after_save=identity(save)
        require(before_driver==after_driver and before_save==after_save,'protected identities unchanged after original SDK')
        check_imports()
        observation={'schema':'xar.original-sdk-current-save-transport/v1','status':'ORIGINAL_SDK_CALL_COMPLETED','machine_id':request['machine_id'],'nonce':request['nonce'],'observed_at_utc':datetime.now(timezone.utc).isoformat(),'worker_source_sha256':request['worker_source_sha256'],'sdk_freeze_ref':request['sdk_freeze_ref'],'validator_ref':request['validator_ref'],'driver_ref':driver_ref,'driver_identity_before':before_driver,'driver_identity_after':after_driver,'save_ref':request['save_ref'],'save_identity_before':before_save,'save_identity_after':after_save,'checkpoint':payload['last_checkpoint'],'anchor':anchor,'pipe_name':request['pipe_name'],'counts':counts,'imported_sources':imports,'Driver_SAVE_body_rewritten':False,'Game_RPC_calls':0}
        if cold_restore:
            observation['schema']='xar.original-sdk-current-save-transport/v2'
            observation['cold_restore_lineage']={'schema':'xar.original-sdk-cold-restore-lineage/v1','format_version':payload.get('format_version'),'bridge_pid':payload.get('bridge_pid'),'episode_character_id':payload.get('episode_character_id'),'episode_run_id':payload.get('episode_run_id'),'succession_lifecycle':payload.get('succession_lifecycle')}
        emit(observation)
except Exception as error:
    emit({'schema':'xar.original-sdk-current-save-transport-failure/v1','status':'REJECTED','observed_at_utc':datetime.now(timezone.utc).isoformat(),'error_type':type(error).__name__,'error':str(error)[:2048],'counts':counts})
    sys.exit(1)
finally:
    sys.setprofile(None)
    for h in reversed(handles): k.CloseHandle(h)
""";
}
