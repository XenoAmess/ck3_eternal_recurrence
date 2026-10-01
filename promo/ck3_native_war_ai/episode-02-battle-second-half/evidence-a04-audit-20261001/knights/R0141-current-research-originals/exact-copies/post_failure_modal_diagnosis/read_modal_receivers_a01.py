"""Authorized bounded RPM only. No injection, calls, writes, windows or input."""
import ctypes as c
from ctypes import wintypes as w
from pathlib import Path
import datetime, hashlib, json, os, struct, sys

OUT = Path(__file__).parent
RAW = Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a05/ck3-state/native-session/ingame-ui-native-results/native-ui-9219ec80c3e8488d8b10a3dde31eee34.json')
RAW_SHA = '32774778FDCC8E8E1FA510CA4D87029756F1FFDEC69B365E5B4A2C96B5AFD765'
EXE_SHA = '2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86'
PID = 6320
K = c.WinDLL('kernel32', use_last_error=True)
K.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];K.OpenProcess.restype=w.HANDLE
K.ReadProcessMemory.argtypes=[w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)];K.ReadProcessMemory.restype=w.BOOL
K.CloseHandle.argtypes=[w.HANDLE];K.CloseHandle.restype=w.BOOL
K.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,c.POINTER(w.DWORD)];K.QueryFullProcessImageNameW.restype=w.BOOL
K.GetProcessTimes.argtypes=[w.HANDLE,c.POINTER(w.FILETIME),c.POINTER(w.FILETIME),c.POINTER(w.FILETIME),c.POINTER(w.FILETIME)];K.GetProcessTimes.restype=w.BOOL
K.CreateToolhelp32Snapshot.argtypes=[w.DWORD,w.DWORD];K.CreateToolhelp32Snapshot.restype=w.HANDLE
class MODULEENTRY32W(c.Structure):
    _fields_=[('dwSize',w.DWORD),('th32ModuleID',w.DWORD),('th32ProcessID',w.DWORD),('GlblcntUsage',w.DWORD),('ProccntUsage',w.DWORD),('modBaseAddr',c.POINTER(c.c_byte)),('modBaseSize',w.DWORD),('hModule',w.HMODULE),('szModule',w.WCHAR*256),('szExePath',w.WCHAR*260)]
K.Module32FirstW.argtypes=[w.HANDLE,c.POINTER(MODULEENTRY32W)];K.Module32FirstW.restype=w.BOOL
K.Module32NextW.argtypes=[w.HANDLE,c.POINTER(MODULEENTRY32W)];K.Module32NextW.restype=w.BOOL

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest().upper()
def ident(p):return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':digest(p)}
report={'schema':'ck3.R0141.readonly-modal-receiver-RPM/v1','scope':'Bounded original GUI singleton/context/header/vector/receiver raw fields. No game API; no native calls; no game writes; no desktop/input.','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':PID,'process_access':'PROCESS_QUERY_INFORMATION|PROCESS_VM_READ (0x0410)','raw_parsed_native_result':ident(RAW),'prior_failed_action_temporal_equivalence':False,'game_date_pause_read_by_this_RPM':False,'reads':[],'passes':[],'failures':[]}
assert report['raw_parsed_native_result']['sha256']==RAW_SHA
original=json.loads(RAW.read_text(encoding='utf-8-sig'))
native=original['original_parsed_command_result']['result']
report['original_failed_action_fields']={k:native[k] for k in ['date_raw','paused','thread_id','gui_context_address','gui_owner_address','rng_owner_thread_id','application_owner_thread_verified','gui_owner_binding_verified','dispatch_invoked','available','unavailable_reason','executable_sha256']}
handle=None
total_read=0
def read(address,size,label):
    global total_read
    assert 0<size<=4096 and total_read+size<=131072
    total_read+=size
    buffer=(c.c_ubyte*size)();done=c.c_size_t();c.set_last_error(0)
    ok=bool(K.ReadProcessMemory(handle,c.c_void_p(address),buffer,size,c.byref(done)))
    item={'sequence':len(report['reads'])+1,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'label':label,'address':address,'address_hex':hex(address),'requested_bytes':size,'read_bytes':done.value,'success':ok and done.value==size,'last_error':c.get_last_error(),'raw_hex':bytes(buffer[:done.value]).hex()}
    report['reads'].append(item)
    if not item['success']:raise RuntimeError('RPM failed '+label+' '+str(item['last_error']))
    return bytes(buffer)
def q(address,label):return struct.unpack('<Q',read(address,8,label))[0]
def receiver(ptr,label):
    item={'address':ptr,'address_hex':hex(ptr),'note':'Names/visibility are widget raw-field observations, not proof of blocking.'}
    vt=q(ptr,label+'.vtable');item['vtable']=vt
    col=q(vt-8,label+'.RTTI_COL_ptr')
    if base<=col<base+module_size:
        colraw=read(col,24,label+'.RTTI_COL')
        signature,offset,cd,td_rva,chd,self_rva=struct.unpack('<6I',colraw)
        item['RTTI_COL_fields']={'signature':signature,'offset':offset,'constructor_displacement':cd,'type_descriptor_rva':td_rva,'hierarchy_rva':chd,'self_rva':self_rva}
        if signature==1 and td_rva<module_size:
            item['RTTI_type_name']=read(base+td_rva+16,192,label+'.RTTI_type_name').split(b'\0',1)[0].decode('ascii',errors='backslashreplace')
    item['raw_widget_flags_D0_D1_D2']=read(ptr+0xD0,3,label+'.widget_flags_D0_D1_D2').hex()
    flags=int(item['raw_widget_flags_D0_D1_D2'][:2],16)
    item['cached_effective_visible_from_D0_bit08']=not bool(flags&8)
    item['local_visible_from_D0_bit10']=not bool(flags&16)
    item['cached_enabled_from_D0_bit02']=not bool(flags&2)
    item['parent_address']=q(ptr+0xE8,label+'.parent')
    s=read(ptr+0x1B8,32,label+'.name_MsvcString_header');ln,cap=struct.unpack_from('<QQ',s,16)
    item['name_length']=ln;item['name_capacity']=cap
    if ln<=256 and cap>=ln and cap<=65536:
        name=s[:ln] if cap<16 else read(struct.unpack_from('<Q',s)[0],max(1,ln),label+'.name_heap')[:ln]
        item['runtime_name']=name.decode('utf-8',errors='backslashreplace')
    else:item['runtime_name_unavailable']='invalid/unverified MSVC string bounds'
    return item

try:
    handle=K.OpenProcess(0x0410,False,PID)
    if not handle:raise OSError(c.get_last_error(),'OpenProcess')
    name=c.create_unicode_buffer(32768);length=w.DWORD(len(name))
    if not K.QueryFullProcessImageNameW(handle,0,name,c.byref(length)):raise OSError(c.get_last_error(),'QueryFullProcessImageNameW')
    exe=Path(name.value);report['actual_process_executable']=ident(exe)
    assert report['actual_process_executable']['sha256']==EXE_SHA
    assert exe.name.lower()=='ck3.exe'
    times=[w.FILETIME() for _ in range(4)]
    if not K.GetProcessTimes(handle,*[c.byref(t) for t in times]):raise OSError(c.get_last_error(),'GetProcessTimes')
    report['process_creation_filetime_100ns']=(times[0].dwHighDateTime<<32)|times[0].dwLowDateTime
    snap=K.CreateToolhelp32Snapshot(0x18,PID)
    if snap==c.c_void_p(-1).value:raise OSError(c.get_last_error(),'Toolhelp')
    try:
        ent=MODULEENTRY32W();ent.dwSize=c.sizeof(ent);ok=K.Module32FirstW(snap,c.byref(ent));mods=[]
        while ok:
            mods.append({'name':ent.szModule,'path':ent.szExePath,'base':c.cast(ent.modBaseAddr,c.c_void_p).value,'bytes':ent.modBaseSize})
            ok=K.Module32NextW(snap,c.byref(ent))
        candidates=[m for m in mods if m['name'].lower()=='ck3.exe']
        assert len(candidates)==1
        module=candidates[0];base=module['base'];module_size=module['bytes'];report['actual_main_module']=module
    finally:K.CloseHandle(snap)
    for pass_number in range(1,3):
        label='pass'+str(pass_number)
        first=q(base+0x576CC68,label+'.global_slot')
        second=q(first+0x1B8,label+'.first_plus_1B8')
        context=q(second+0x58,label+'.second_plus_58_CONTEXT')
        host=q(context+0x3D0,label+'.context_plus_3D0_host')
        owner=q(host+8,label+'.host_plus_08_OWNER')
        item={'pass':pass_number,'first':first,'second':second,'context':context,'owner_lookup_host':host,'owner':owner,'matches_failed_action_context':context==native['gui_context_address'],'matches_failed_action_owner':owner==native['gui_owner_address']}
        assert item['matches_failed_action_context'] and item['matches_failed_action_owner']
        header=read(context+0x290,16,label+'.modal_receiver_vector_header')
        data,capacity,count=struct.unpack('<Qii',header)
        item.update({'modal_vector_data_address':data,'raw_int32_at_298':capacity,'modal_receiver_count_int32_at_29C':count,'receivers':[]})
        report['passes'].append(item)
        assert 0<=count<=256 and (count==0 or data!=0)
        if count:
            pointers=struct.unpack('<'+'Q'*count,read(data,count*8,label+'.modal_vector_entries'))
            for index,ptr in enumerate(pointers):
                assert ptr
                item['receivers'].append(receiver(ptr,label+'.receiver'+str(index)))
            item['absolute_top_receiver_address']=pointers[-1]
        else:item['absolute_top_receiver_address']=None
    report['two_passes_stable']=report['passes'][0]|{'pass':2}==report['passes'][1]
    report['status']='READONLY_CURRENT_MEMORY_CAPTURED'
except BaseException as exc:
    report['status']='READONLY_DIAGNOSIS_RED'
    report['failures'].append({'exception_type':type(exc).__name__,'message':str(exc)})
finally:
    if handle:report['CloseHandle_success']=bool(K.CloseHandle(handle))
    report['ended_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    report['total_RPM_bytes']=total_read;report['script']=ident(Path(__file__))
    target=OUT/'readonly-modal-receivers-a01.json'
    with target.open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'report':ident(target),'status':report['status'],'passes':[{'count':p.get('modal_receiver_count_int32_at_29C'),'receivers':[{'name':r.get('runtime_name'),'visible':r.get('cached_effective_visible_from_D0_bit08'),'RTTI':r.get('RTTI_type_name')} for r in p['receivers']]} for p in report['passes']],'failures':report['failures']},ensure_ascii=False))
sys.exit(0 if report['status']=='READONLY_CURRENT_MEMORY_CAPTURED' else 2)
