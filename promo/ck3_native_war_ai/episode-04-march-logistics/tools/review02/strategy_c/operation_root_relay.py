"""Explicit C operation relay, migrated from the frozen Root IO methods.
Normal constructor only; no SDK, game launcher, AST rewriting or inherited constructor bypass.
The frozen source remains unchanged. Whole-S0 equality and fresh arrival are still checked by C stages.
"""
from __future__ import annotations
import argparse,ctypes,hashlib,importlib.util,json,re,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path

VERIFY_REL='promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/locked_routes/verify.py'
MAX_RESPONSE=16*1024*1024

def need(ok,message):
    if not ok:raise RuntimeError(message)
def utc():return datetime.now(timezone.utc).isoformat()
def load(path,limit=MAX_RESPONSE):
    path=Path(path);need(path.stat().st_size<=limit,'bounded input too large: '+str(path))
    raw=path.read_bytes();need(len(raw)<=limit,'input grew past bound')
    return json.loads(raw.decode('utf-8-sig'))
def pin(path,limit=MAX_RESPONSE):
    path=Path(path);need(path.stat().st_size<=limit,'pin input too large')
    raw=path.read_bytes();return {'path':str(path.resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write_new(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    need(len(raw)<=1024*1024,'derived receipt too large')
    with path.open('xb') as stream:stream.write(raw)
    return path
def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
def process_time(pid):
    from ctypes import wintypes as W
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
    k.GetProcessTimes.argtypes=[W.HANDLE,*([ctypes.POINTER(W.FILETIME)]*4)];k.GetProcessTimes.restype=W.BOOL
    k.CloseHandle.argtypes=[W.HANDLE];k.CloseHandle.restype=W.BOOL
    h=k.OpenProcess(0x1000,False,pid);need(bool(h),'owned PID not alive/readable')
    try:
        values=[W.FILETIME() for _ in range(4)]
        need(k.GetProcessTimes(h,*[ctypes.byref(v) for v in values]),'actual process creation time unavailable')
        return values[0].dwLowDateTime|(values[0].dwHighDateTime<<32)
    finally:k.CloseHandle(h)


OPERATION_BINDING_API='xar.e04.C.root-operation-relay.v1'

class Live:
    def __init__(self,args,*,transport=None,process_probe=process_time,machine_probe=None,clock=None):
        self.args=args;self.repo=args.repo.resolve();self.process_probe=process_probe
        self.context_path=args.context.resolve();self.assets=self.context_path.parent
        # Every constructor input is metadata, exact-pinned before import/use.
        gpath=Path(args.runtime_guard).resolve()
        need(pin(gpath,1024*1024)['sha256']==args.runtime_guard_sha256,'shared runtime guard source changed')
        g=module(gpath,'C_qualified_operation_guard')
        self.c,_=g._read_pinned(args.context,args.context_sha256)
        p,proof_pin=g._read_pinned(args.runtime_proof,args.runtime_proof_sha256)
        plan,plan_pin=g._read_pinned(args.plan,args.plan_sha256)
        prepared,prepared_pin=g._read_pinned(args.prepared,args.prepared_sha256)
        now=(clock or (lambda:datetime.now(timezone.utc)))()
        self.machine=(machine_probe or g.current_machine_id)(self.repo)
        identity=self.c.get('identity') or {}
        runtime=args.runtime
        need(type(runtime) is dict,'explicit cold runtime metadata required')
        self.live_operation_guard=g.OperationGuard(args.live_binding,args.live_binding_sha256,
            context=self.c,runtime=g.proof_runtime(p),scene_root=self.assets,
            source_head=args.source_head,machine_id=self.machine,run_id=args.run_id,
            max_runtime_total_bytes=args.max_runtime_total_bytes,deadline_utc=args.deadline_utc,
            normal_save_sha256=args.loaded_save_sha256,clock=clock)
        guard=self.live_operation_guard
        need(args.run_sequence==guard.binding['run_sequence'],'allocated run sequence differs')
        self.deadline=g.timestamp(guard.binding['deadline_utc'])
        need(plan.get('status')=='frozen' and (plan.get('strategies') or {}).get('C',{}).get('mode')=='whole-via',
             'formal frozen C policy required before constructor')
        build=plan.get('build') or {}
        need(build.get('source_head')==runtime.get('source_head')==p.get('source_head')==args.source_head,
             'plan/runtime/proof actual source differs')
        need(type(build.get('native_dll_sha256')) is str and g.sha(build['native_dll_sha256'])
             and runtime.get('native_dll_sha256')==build['native_dll_sha256'],'plan/runtime actual DLL differs')
        normal=plan.get('normal_save') or {}
        need(normal.get('kind')=='normal-native-checkpoint' and normal.get('sha256')==args.loaded_save_sha256
             and type(normal.get('bytes')) is int and normal['bytes']>0,'frozen normal S0 input missing/different')
        frozen,started=g.timestamp(plan.get('frozen_at_utc')),g.timestamp(runtime.get('started_at_utc'))
        need(frozen<started<=g.timestamp(guard.document['created_at_utc'])<=now,
             'independent cold runtime did not start after frozen plan; continuation is not a fresh arm')
        need(type(prepared.get('prepared_at')) is str and g.timestamp(prepared['prepared_at'])<=started,
             'normal preparation must precede this cold runtime')
        need(prepared.get('machine_id')==self.machine and type(prepared.get('assets_root')) is str
             and Path(prepared['assets_root']).resolve()==self.assets,'prepared normal load belongs to another machine/scene')
        state=prepared.get('state_dir')
        need(type(state) is str and Path(state).is_absolute(),'exact prepared state_dir must be absolute')
        self.state_dir=Path(state).resolve()
        self.native_session=(self.state_dir/'native-session').resolve()
        need(self.state_dir!=self.assets and self.state_dir.is_relative_to(self.assets)
             and self.native_session.is_relative_to(self.assets),'prepared state/native-session escapes adopted scene')
        need(self.state_dir.is_dir(),'actual prepared state directory missing')
        source=(prepared.get('checkpoint') or {}).get('source') or {}
        save=source.get('save') or {}
        need(save.get('sha256')==normal['sha256'] and save.get('bytes',save.get('size'))==normal['bytes']
             and source.get('date_raw')==plan.get('t0_raw')
             and source.get('actor_id')==guard.runtime['actor'],'normal prepared save/date/actor differs from frozen S0')
        for life in (prepared.get('succession_lifecycle'),source.get('source_lifecycle')):
            need(type(life) is dict and life.get('lifecycle')=='ordinary_campaign_succession'
                 and life.get('xar_enabled')=='xar_off','normal source/load lifecycle unavailable or not ordinary xar_off')
        need(p.get('machine_id')==self.machine and p.get('run_id')==args.run_id,'actual proof belongs to another machine/run')
        intent=p.get('stable_character_intent') or {}
        need(intent.get('historical_id')==1128
             and intent.get('bookmark_character_name_key')=='bookmark_rags_to_riches_duke_robert',
             'normal Robert source intent missing; no runtime ID inference')
        need(type(args.army_id) is int and 0<=args.army_id<2**31,'actual public Army FullID required')
        need(args.card=='C','operation relay is the explicit C binding, not a new public planner')
        head=subprocess.run(['git','-C',str(self.repo),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
        need(head==args.source_head,'actual reviewed checkout differs')
        need((self.repo/VERIFY_REL).is_file(),'repository portable verifier missing')
        self.run=(self.assets/args.run_id).resolve()
        need(self.run.is_relative_to(self.assets),'allocated run escapes admitted scene')
        need(self.run.is_dir() and (self.run/'requests').is_dir() and (self.run/'responses').is_dir(),
             'Root allocated run/request/response directories missing')
        self.binding={**guard.runtime,'army_id':args.army_id,'native_carmy_id':None}
        self.proof_pin=proof_pin
        self.helper_pin=pin(args.request_helper,65536)
        need(self.helper_pin['sha256']==args.request_helper_sha256,'Root request helper changed')
        need(all(type(s) is str and re.fullmatch('[A-Za-z][A-Za-z0-9_-]{0,47}',s)
                 for s in (args.case_id,args.attempt)),'safe independent C case/attempt required')
        self.ledger=self.assets/'strategy-c-phased-a03';self.case=self.ledger/args.case_id
        fixed=self.case/'operation-binding.actual.json'
        fixed_value={'schema':OPERATION_BINDING_API,'live_binding':guard.pin,'capacity':guard.capacity_pin,
            'context':pin(args.context,1024*1024),'runtime_proof':proof_pin,'plan':plan_pin,'prepared':prepared_pin,
            'runtime':runtime,'binding':self.binding,'deadline_utc':self.deadline.isoformat(),
            'request_helper':self.helper_pin,'constructor':pin(Path(__file__),1024*1024)}
        if fixed.exists():need(load(fixed,1024*1024)==fixed_value,'C case operation/source/S0/lifetime changed')
        else:need(not self.case.exists(),'existing historical/other C case cannot adopt a new operation')
        saved=self.case/'binding.actual.json'
        if saved.exists():
            prior=load(saved,1024*1024)
            need(prior.get('live_operation_binding')==guard.pin and prior.get('case')=='C'
                 and prior.get('deadline_utc')==self.deadline.isoformat(),'C saved runtime/operation changed')
            need(all(prior['binding'].get(k)==v for k,v in self.binding.items() if k!='native_carmy_id'),
                 'C saved PID/create/gen/episode/Army differs')
            self.binding=prior['binding']
        self.check_process()
        self.v=module(self.repo/VERIFY_REL,'C_existing_frame_reader')
        self.transport=transport if transport is not None else module(args.request_helper,'C_existing_Root_file_transport')
        need(Path(self.transport.RUN).resolve()==self.run and Path(self.transport.ASSETS).resolve()==self.assets
             and self.transport.CONTEXT==self.c,'Root transport run/assets/context differs')
        self.case.mkdir(parents=True,exist_ok=True)
        if not fixed.exists():write_new(fixed,fixed_value)
        self.attempt=self.case/args.attempt;self.attempt.mkdir(exist_ok=False)
        self.pending=False;self.serial=0;self.last=None;self._refs={}
        self.runtime_total_budget_bytes=args.max_runtime_total_bytes
        self.meta={'machine_id':self.machine,'source_head':args.source_head,'at_utc':utc(),
            'run_id':args.run_id,'case':'C','case_id':args.case_id,'stage':args.stage,
            'helper':pin(Path(__file__),1024*1024),'runtime_proof':proof_pin,'request_helper':self.helper_pin,
            'live_operation_binding':guard.pin,'capacity_admission':guard.capacity_pin,
            'deadline_utc':self.deadline.isoformat(),'phases_chained':False,
            'SDK_connection_created':False,'capture_started':False,'unknown_action_retry':False,
            'fresh_C_arm_qualified':False,'R10_completed':False}
        write_new(self.attempt/'START.actual.json',{**self.meta,'binding':self.binding})
    def check_process(self):
        need(self.process_probe(self.binding['pid'])==self.binding['process_create_time_100ns'],'actual PID/create-time differs from runtime proof')

    def used_bytes(self):
        seen=set();total=0
        for root in (self.run,self.ledger,self.native_session):
            if not root.exists():continue
            for path in root.rglob('*'):
                if not path.is_file():continue
                actual=path.resolve();need(actual.is_relative_to(self.assets),'runtime file escapes adopted scene')
                if actual in seen:continue
                seen.add(actual);need(len(seen)<=50000,'finite runtime file count reached')
                total+=path.stat().st_size
        return total
    def request(self,name,tool,arguments):
        self.live_operation_guard.check();self.check_process();self.serial+=1
        identifier=self.args.attempt+'-'+str(self.serial).zfill(3)+'-'+name
        req=self.run/'requests'/(identifier+'.json');response=self.run/'responses'/req.name
        need(not req.exists() and not response.exists(),'exact request exists; inspect original, never replay')
        reserve=MAX_RESPONSE+65536+(MAX_RESPONSE if tool=='ck3_query_army_strengths' else 0)
        need(self.used_bytes()+reserve<=self.runtime_total_budget_bytes,'finite runtime cannot reserve next response/Driver result')
        self.pending=True
        try:row=self.transport.request(identifier,tool,arguments,timeout=90)
        finally:self.pending=not response.exists()
        need(response.exists() and response.stat().st_size<=MAX_RESPONSE,'response absent or exceeds bounded stopline')
        need(self.used_bytes()<=self.runtime_total_budget_bytes,'runtime total crossed bound; preserve original, never retry')
        need(row.get('machine_id')==self.machine and row.get('is_error') is False
             and row.get('request',{}).get('request_id')==identifier,'response error/machine/request differs')
        return row,pin(req),pin(response)
    def snap(self,name,*,paused=True):
        row,_,ref=self.request(name,'ck3_take_snapshot',{'include_native_command_history':False})
        s=row['body'];d=s.get('diagnostics') or {};a=s.get('played_character') or {}
        need(d.get('bridge_pid')==self.binding['pid'] and d.get('connection_generation')==self.binding['generation']
             and s.get('episode_run_id')==self.binding['episode'] and a.get('character_id')==self.binding['actor']
             and a.get('alive') is True and s.get('map_ready') is True,'fresh snapshot runtime/owner differs')
        need(not s.get('active_event') and not s.get('pending_character_interaction'),'modal requires Root existing native policy; no replay')
        if paused:need(s.get('paused') is True,'actual paused frame required')
        self.last=s;return s,ref
    def frame(self,name):
        s,sref=self.snap(name+'-before')
        return self.strength_at(s,sref,name+'-army')
    def strength_at(self,s,sref,name):
        row,_,_=self.request(name,'ck3_query_army_strengths',{'army_ids':[self.binding['army_id']],
            'expected_revision':s['revision'],'profile':'ordinary_core_v1'})
        ev=row.get('army_history_evidence');need(type(ev) is dict,'response-local raw Driver reference missing; no glob/latest fallback')
        ref=ev['raw_result_reference'];path=Path(ref['path'])
        need(path.is_absolute() and path.parent.resolve()==(self.native_session/'army-query-history-results').resolve()
             and ref.get('kind')=='complete-driver-army-query-result-json-v1' and ref.get('wire_bytes_preserved') is False,
             'actual scoped Driver reference parent/kind differs')
        actual=pin(path);need(actual['bytes']==ref['bytes'] and actual['sha256']==ref['sha256'],'raw Driver reference bytes/SHA differs')
        q=load(path)
        need(q.get('army_strengths_profile')=='ordinary_core_v1' and q.get('query_sequence')==ev.get('query_sequence')
             and ev.get('machine_id')==self.machine and ev.get('request_id')==row['request']['request_id'],'query response-local profile/sequence differs')
        scope=q.get('army_strengths_query_scope') or {};need(scope.get('army_ids')==[self.binding['army_id']],'native selected-Army scope differs')
        rows=q.get('army_strengths');need(type(rows) is list and len(rows)==1 and rows[0].get('army_id')==self.binding['army_id'],'unexpected Army row scope')
        if self.binding['native_carmy_id'] is None:
            full=rows[0].get('native_carmy_id');need(type(full) is int and full>0,'actual native Army identity absent')
            self.binding['native_carmy_id']=full
            write_new(self.case/'binding.actual.json',{**self.meta,'binding':self.binding})
        observation=self.v.frame(s,q,self.binding)
        refs={'snapshot':sref,'strength':actual}
        self._refs[s['snapshot_id']]=refs
        return observation,refs
    def coherent_stop_core(self,stopped,name,stopped_ref=None):
        # Status publication may change a revision. Read a fresh complete pair
        # from the actual prepared session; never adopt an old state-a01 path.
        need(stopped.get('paused') is True,'original stopped frame must be paused')
        originals=[a for a in stopped.get('player_armies',[]) if a.get('army_id')==self.binding['army_id']]
        need(len(originals)==1,'original stopped Army absent or ambiguous')
        fresh,ref=(stopped,stopped_ref) if stopped_ref is not None else self.snap(name+'-fresh')
        current=[a for a in fresh.get('player_armies',[]) if a.get('army_id')==self.binding['army_id']]
        keys=('army_id','owner_character_id','controllable','current_province_id',
              'army_state','army_state_code','route_province_ids','route_read_status',
              'route_source_count','move_target_province_id','move_target_observable',
              'in_combat','retreating')
        need(fresh.get('paused') is True and fresh.get('date_raw')==stopped.get('date_raw')
             and len(current)==1 and all(current[0].get(k)==originals[0].get(k) for k in keys),
             'fresh post-status Army/date/state differs from original paused stop')
        return self.strength_at(fresh,ref,name+'-core')
    def claim(self,kind,detail):
        path=self.case/(kind+'.once.claim.json')
        write_new(path,{**self.meta,'binding':self.binding,'kind':kind,'request_outcome':'not_yet_known',**detail})
        return path
    def action(self,kind,tool,arguments,detail):
        identifier=self.args.attempt+'-'+str(self.serial+1).zfill(3)+'-'+kind
        self.claim(kind,{**detail,'tool':tool,'arguments':arguments,'request_id':identifier,
            'request_path':str(self.run/'requests'/(identifier+'.json')),
            'response_path':str(self.run/'responses'/(identifier+'.json'))})
        row,request,response=self.request(kind,tool,arguments)
        need(row['body'].get('accepted') is True,'action rejected/unknown; no automatic retry')
        value={**self.meta,'binding':self.binding,'request':request,'response':response,'accepted':True,**detail}
        write_new(self.case/(kind+'.ack.actual.json'),value);return value
    def action_original(self,kind):
        claim=load(self.case/(kind+'.once.claim.json'),1024*1024)
        ack=self.case/(kind+'.ack.actual.json')
        if not ack.exists():
            original=Path(claim['response_path'])
            need(original.exists(),'original action response still pending; resolve exact original request, never repeat action')
            envelope=load(original)
            need(envelope.get('machine_id')==self.machine and envelope.get('is_error') is False
                 and envelope.get('request',{}).get('request_id')==claim['request_id']
                 and envelope.get('body',{}).get('accepted') is True,
                 'original response rejected/unknown; preserve diagnostics and do not advance automatically')
            write_new(ack,{**claim,'request':pin(claim['request_path']),'response':pin(original),
                'accepted':True,'late_original_response_read_only_recovery':True})
        value=load(ack,1024*1024)
        need(value['binding']==self.binding and claim['binding']==self.binding,'action not same runtime')
        return value
