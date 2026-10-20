"""Finite real Win32 transport fixtures; no Game, Native DLL, SDK or Task run."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import site
import subprocess
import sys
import threading
import time
import types

OWN=Path(__file__).resolve().parent
sys.path.insert(0,str(OWN))
import prepare_source26_startup_timeout_v1 as producer
MACHINE='xenoamess-full-tower-eb9d2c1186'
BASE=Path('C:/Users/xenoa/AppData/Local/Programs/Python/Python313/python.exe')
PREP=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep')
SDK=PREP/'sdk-v20261019-candidate/src20'
OLD=PREP/'robert30-v20261019-campaign01/runtime-a04'
CARD=Path('D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/A05-SOURCE26-SOURCE-QUALIFICATION704KiB0630-ADMITTED01.json')
CARD_PIN=(4327,'530bb027b1832a39a29de60ac534b23ad60039b3ff545ad6fb341f009d35360e')
ARTIFACT=CARD.parent/'A05-SOURCE26-QUALIFICATION0630-01/controls'


def require(ok,why):
    if not ok:raise ValueError('Source26 transport qualification denied: '+why)


def stamp():return datetime.now(timezone.utc).isoformat()


def pin(path):
    path=Path(path).resolve();raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':producer.sha(raw)}


def modules():
    sys.path.insert(0,str(SDK));sys.path.insert(0,str(OWN.parent))
    site.addsitedir(str(OWN.parent/'.venv/Lib/site-packages'))
    import xar_autoplayer.bridge
    data=producer.compose_sdk({name:(SDK/name).read_bytes() for name in producer.SDK_PINS})
    loaded=[]
    for relative,raw in data.items():
        name=relative[:-3].replace('/','.')
        module=types.ModuleType(name);module.__package__=name.rsplit('.',1)[0]
        module.__file__=str(SDK/relative)
        sys.modules[name]=module
        exec(compile(raw,'RAM-Source26/'+relative,'exec'),vars(module));loaded.append(module)
    return loaded


def transport(startup=120.0):
    io_module,origin=modules()
    from xar_autoplayer.bridge.native_loaded_provider_windows_v1 import WindowsNativeCustodyFacadeV1
    facade=WindowsNativeCustodyFacadeV1(enabled=True)
    io=io_module.OriginKernelIOV1(facade,enabled=True,startup_timeout=startup)
    require(io.timeout==10.0 and io.startup_timeout==startup,'separate steady/startup budgets')
    return io,origin


def close_all(io):
    for handle in tuple(io.facade._owned):io.close(handle)
    require(not io.facade._owned and not io._holders,'all fixture-owned kernel handles released')


def peer(args):
    io,origin=transport()
    try:
        if args.case=='connected':time.sleep(12.0)
        control=io.client(args.pipe)
        io.send(control,{'kind':'staged','role':'MCPApp','epoch':origin._epoch(),'creator':'0'*64})
        require(io.recv(control,startup=True)=={'kind':'parent_accepted','epoch':origin._epoch(),'creator':'0'*64},
            'actual parent bootstrap response')
        if args.case=='export':time.sleep(12.0)
        io.send(control,{'kind':'actual_child_exports','exports':[]})
        require(io.recv(control)=={'done':True},'parent completed actual export pull')
    finally:close_all(io)
    print(json.dumps({'peer':'PASS','pid':os.getpid(),'owned_after':0}))


def fixture(case):
    io,origin=transport();server,name=io.server()
    holder=types.SimpleNamespace(_owned=[],_creator_source_digest_v1='0'*64)
    command=[str(BASE),'-B','-S','-X','utf8',str(Path(__file__).resolve()),'--peer','--case',case,'--pipe',name]
    child=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    started=time.monotonic();record_end=None;pull_end=None
    try:
        edge=origin._record_actual_child_v1(holder,io,child,int(child._handle),server,'MCPApp')
        record_end=time.monotonic()-started
        handles=origin._pull_actual_chain_v1(edge)
        pull_end=time.monotonic()-started
        require(len(handles)==1,'real direct child retained once')
        io.send(server,{'done':True})
        out,err=child.communicate(timeout=20)
        require(child.returncode==0 and not err,'actual peer exited zero: '+err.decode('utf-8',errors='replace')[:1200])
        elapsed=record_end if case=='connected' else pull_end-record_end
        require(11.5<=elapsed<120,'real delay exceeds old 10s but remains within explicit120')
        return {'case':case,'status':'PASS','command':command,'actual_child_pid':child.pid,
            'record_seconds':record_end,'pull_total_seconds':pull_end,'delayed_phase_seconds':elapsed,
            'child_exit':child.returncode,'child_stdout':out.decode('utf-8'),'owned_after':0,
            'calls':'actual _record_actual_child_v1 and _pull_actual_chain_v1',
            'holder_scope':'synthetic transport holder, no preload custody/provider qualification'}
    finally:
        if child.poll() is None:
            child.terminate();child.wait(timeout=10)
        close_all(io);child._handle.Close()


def negative():
    io,origin=transport(.15);server,name=io.server();started=time.monotonic()
    try:
        try:io.connected(server)
        except OSError:pass
        else:raise ValueError('unconnected startup must time out')
        duration=time.monotonic()-started
        require(.12<=duration<2,'finite startup timeout enforced')
    finally:close_all(io)
    io,origin=transport();server,name=io.server();client=io.client(name);io.connected(server)
    holder=types.SimpleNamespace(_owned=[])
    root=object.__new__(origin._CanonicalOriginV1)
    root.lock=threading.RLock();root.active=True;root.io=io;root.server=server
    root.revoke_handle=io.event(holder=holder)
    try:
        root.revoke_before_close()
        require(root.active is False and io.api.wait_zero(root.revoke_handle)==0,'actual revoke event signaled')
        try:io.recv(client)
        except OSError:pass
        else:raise ValueError('revoked private server must reject client read')
    finally:close_all(io)
    for value in (0,301,True):
        try:transport(value)
        except ValueError:pass
        else:raise ValueError('invalid startup bound accepted')
    return {'case':'negative','status':'PASS','finite_timeout_seconds':duration,'revoked_read_rejected':True,
        'once_only_source_preserved':True,'owned_after':0,'custody_constructed':False}


def wiring():
    data=producer.compose_sdk({name:(SDK/name).read_bytes() for name in producer.SDK_PINS})
    host=producer.compose_host((OWN/'canonical_native_provider_chain_v1.py').read_bytes())
    outer=producer.compose_outer((OLD/'root_c23_canonical_outer.py').read_bytes(),host)
    io,origin=transport()
    try:
        require(inspect.signature(type(io)).parameters['startup_timeout'].default==10.0,'default remains10')
        require(inspect.signature(type(io).recv).parameters['startup'].default is False,'steady recv remains default')
        require(outer.count(b'startup_timeout=120.0')==3,'all three actual outer caller opt-ins')
        require(producer.sha(host).encode() in outer,'actual creator source-map SHA updated')
        require(host.count(b'startup_timeout=10.0')==3,'all three host entry defaults preserved')
        require(b'reply=self.io.recv(self.handle)' in data[producer.SDK_ORIGIN], 'steady origin reply unchanged')
    finally:close_all(io)
    return {'case':'wiring','status':'PASS','SDK':{n:{'bytes':len(b),'sha256':producer.sha(b)} for n,b in data.items()},
        'host':{'bytes':len(host),'sha256':producer.sha(host)},'outer':{'bytes':len(outer),'sha256':producer.sha(outer)},
        'all_outer_optins':120,'max_startup':300,'default_startup':10,'steady_timeout':10,'owned_after':0}


def once(path,value):
    data=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    require(len(data)<=65536,'bounded qualification receipt')
    with path.open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
    require(path.read_bytes()==data,'actual receipt readback')


def run():
    card_raw=CARD.read_bytes();require((len(card_raw),producer.sha(card_raw))==CARD_PIN,'actual source/qualification card')
    card=json.loads(card_raw);require(card.get('machine_id')==MACHINE,'actual machine admission')
    require(datetime.now(timezone.utc)<datetime.fromisoformat('2026-10-20T06:30:00+00:00'),'review deadline')
    require(Path(sys.executable).resolve()==BASE and sys.flags.no_site==1,'actual direct base -S runner required')
    ARTIFACT.mkdir(parents=True,exist_ok=True)
    require(not (ARTIFACT/'QUALIFIED.json').exists(),'once-only final receipt')
    jobs=[]
    for case in ('connected','export'):
        command=[str(BASE),'-B','-S','-X','utf8',str(Path(__file__).resolve()),'--fixture','--case',case]
        stdout=(ARTIFACT/(case+'.stdout.json')).open('xb');stderr=(ARTIFACT/(case+'.stderr.log')).open('xb')
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr);jobs.append((case,command,child,stdout,stderr))
    rows=[wiring(),negative()]
    for case,command,child,stdout,stderr in jobs:
        code=child.wait(timeout=150);stdout.close();stderr.close()
        require(code==0,'fresh fixture failed: '+case+'; retain exact stdout/stderr')
        row=json.loads((ARTIFACT/(case+'.stdout.json')).read_bytes());row['fixture_command']=command;rows.append(row)
    result={'schema':'xar.source26.startup-transport-qualified/v1','machine_id':MACHINE,'observed_at_utc':stamp(),
        'status':'REAL_WIN32_DELAYED_STARTUP_TRANSPORT_PASS','source_card':pin(CARD),
        'producer':pin(OWN/'prepare_source26_startup_timeout_v1.py'),'qualification_source':pin(__file__),
        'command':[str(BASE),'-B','-S','-X','utf8',str(Path(__file__).resolve())], 'rows':rows,
        'scope':{'actual_Win32_named_pipes':True,'real_fixture_processes':4,'Game':0,'Task':0,'Native_DLL':0,
            'SDK_owner':0,'Game_RPC':0,'Source26_export':0,'runtime_writes':0,'mock_transport':False,
            'synthetic_holder_is_not_loaded_provider_qualification':True,'all_owned_after':0}}
    once(ARTIFACT/'QUALIFIED.json',result)
    allocation=sum(((p.stat().st_size+4095)//4096)*4096 for p in ARTIFACT.iterdir() if p.is_file())
    require(allocation+32768<=196608,'admitted artifact allocation/FS cap')
    print(json.dumps({'receipt':pin(ARTIFACT/'QUALIFIED.json'),'allocation':allocation,'FS_upper':32768,'rows':rows}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--peer',action='store_true')
    parser.add_argument('--fixture',action='store_true');parser.add_argument('--case',choices=('connected','export'))
    parser.add_argument('--pipe');args=parser.parse_args()
    if args.peer:peer(args)
    elif args.fixture:print(json.dumps(fixture(args.case)))
    else:run()
