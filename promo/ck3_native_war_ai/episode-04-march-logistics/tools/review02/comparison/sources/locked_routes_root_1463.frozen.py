"""Root-invoked staged file relay. Import is offline; no SDK or phase chaining.

Unknown actions retain their once claim. Only a later explicit readback phase
may inspect the original response. This module never starts CK3 or recording.
"""
from __future__ import annotations
import argparse,ctypes,hashlib,importlib.util,json,re,subprocess,sys,time
from datetime import datetime,timezone
from pathlib import Path

SOURCE='1463bd9b4b89612d283dd45ac4ec9efbf22f048d'
TARGET_ASSETS='live12004-locked-route-a01'
VERIFY_REL='promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/locked_routes/verify.py'
MAX_RESPONSE=16*1024*1024
RUN_BUDGET=512*1024*1024

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

class Live:
    def __init__(self,args,*,transport=None,process_probe=process_time):
        self.args=args;self.repo=args.repo.resolve();self.process_probe=process_probe
        need((self.repo/VERIFY_REL).is_file(),'existing repository portable verifier missing')
        head=subprocess.run(['git','-C',str(self.repo),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
        need(head==SOURCE,'source checkout differs from frozen1463')
        self.v=module(self.repo/VERIFY_REL,'root_repo_locked_routes_verify')
        self.context_path=args.context.resolve();self.c=load(self.context_path,1024*1024)
        self.deadline=datetime.fromisoformat(args.deadline_utc.replace('Z','+00:00'))
        need(self.deadline.tzinfo is not None,'original admitted deadline must have explicit timezone')
        identity=self.c['identity'];self.machine=self.c['machine_id']
        need(self.machine=='desktop-3fevhd2-1c74096080' and identity['machine_id']==self.machine
             and identity['mod_key']=='vanilla' and self.c['source_head']==SOURCE,'allocation source/machine differs')
        self.assets=self.context_path.parent;need(self.assets.name==TARGET_ASSETS,'only next admitted locked-route assets supported')
        self.run=self.assets/identity['run_id'];need(self.run.is_dir(),'Root allocated live run not present')
        proof_pin=pin(args.runtime_proof,1024*1024)
        need(proof_pin['sha256']==args.runtime_proof_sha256,'actual runtime proof changed')
        p=load(args.runtime_proof,1024*1024)
        need(p['machine_id']==self.machine and p['source_head']==SOURCE and p['run_id']==identity['run_id']
             and p['stable_character_intent']['historical_id']==1128
             and p['stable_character_intent']['bookmark_character_name_key']=='bookmark_rags_to_riches_duke_robert',
             'actual new normal Robert runtime proof absent/wrong')
        self.binding={'pid':p['pid'],'process_create_time_100ns':p['process_creation_filetime_100ns'],
            'generation':p['connection_generation'],'actor':p['actual_runtime_character_full_id'],
            'episode':p['episode_run_id'],'army_id':args.army_id,'native_carmy_id':None}
        need(all(type(self.binding[k]) is int and self.binding[k]>0 for k in ('pid','process_create_time_100ns','actor','army_id')),
             'runtime positive identities missing')
        need(type(self.binding['generation']) is int and self.binding['generation']>=0,'actual connection generation missing')
        self.proof_pin=proof_pin
        self.helper_pin=pin(args.request_helper,64*1024)
        need(self.helper_pin['sha256']==args.request_helper_sha256,'reviewed Root relay helper changed')
        self.transport=transport if transport is not None else module(args.request_helper.resolve(),'root_existing_locked_route_relay')
        need(Path(self.transport.RUN).resolve()==self.run.resolve()
             and Path(self.transport.ASSETS).resolve()==self.assets.resolve()
             and self.transport.CONTEXT['identity']['run_id']==identity['run_id']
             and self.transport.CONTEXT['machine_id']==self.machine,'Root relay runtime path/identity differs')
        need(re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,47}',args.case_id) is not None
             and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,47}',args.attempt) is not None,'explicit safe case/attempt required')
        self.ledger=self.assets/'locked-routes-helper-a02';self.case=self.ledger/args.case_id
        self.case.mkdir(parents=True,exist_ok=True);self.attempt=self.case/args.attempt;self.attempt.mkdir(exist_ok=False)
        self.pending=False;self.serial=0;self.last=None
        saved=self.case/'binding.actual.json'
        if saved.exists():
            prior=load(saved,1024*1024)
            need(prior.get('case')==args.card,'R12/R13 require independent case identities and normal initial Moves')
            need(prior.get('deadline_utc')==self.deadline.isoformat(),'case deadline changed; original deadline cannot be extended')
            for key,value in self.binding.items():
                if key!='native_carmy_id':need(prior['binding'][key]==value,'case crossed owned runtime')
            self.binding=prior['binding']
        self.meta={'machine_id':self.machine,'source_head':SOURCE,'at_utc':utc(),
            'run_id':identity['run_id'],'helper':pin(Path(__file__),1024*1024),'runtime_proof':proof_pin,
            'request_helper':self.helper_pin,'portable_verifier':pin(self.repo/VERIFY_REL,1024*1024),
            'case_id':args.case_id,'case':args.card,'stage':args.stage,'phases_chained':False,
            'deadline_utc':self.deadline.isoformat(),'other_artifact_budget_bytes':RUN_BUDGET,
            'SDK_connection_created':False,'capture_started':False,'unknown_action_retry':False}
        if args.stage!='report':self.check_process()
        write_new(self.attempt/'START.actual.json',{**self.meta,'binding':self.binding})
    def check_process(self):
        need(self.process_probe(self.binding['pid'])==self.binding['process_create_time_100ns'],'actual PID/create-time differs from runtime proof')
    def used_bytes(self):
        total=0;count=0
        for directory in (self.run/'requests',self.run/'responses'):
            for p in directory.iterdir():
                if p.is_file():total+=p.stat().st_size;count+=1
        for p in self.ledger.rglob('*.json'):
            total+=p.stat().st_size;count+=1
        need(count<=20000,'finite admitted case metadata count reached')
        return total
    def request(self,name,tool,arguments):
        need(datetime.now(timezone.utc)<=self.deadline,'original admitted deadline reached; no new request')
        self.check_process();self.serial+=1
        identifier=self.args.attempt+'-'+str(self.serial).zfill(3)+'-'+name
        req=self.run/'requests'/(identifier+'.json');response=self.run/'responses'/req.name
        need(not req.exists() and not response.exists(),'exact request exists; inspect original, never replay')
        need(self.used_bytes()+MAX_RESPONSE+65536<=RUN_BUDGET,'admitted512MiB budget cannot reserve next packet')
        self.pending=True
        try:row=self.transport.request(identifier,tool,arguments,timeout=90)
        finally:self.pending=not response.exists()
        need(response.exists() and response.stat().st_size<=MAX_RESPONSE,'response absent or exceeds16MiB stopline')
        need(self.used_bytes()<=RUN_BUDGET,'512MiB stopline reached')
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
        row,_,_=self.request(name+'-army','ck3_query_army_strengths',{'army_ids':[self.binding['army_id']],
            'expected_revision':s['revision'],'profile':'ordinary_core_v1'})
        ev=row.get('army_history_evidence');need(type(ev) is dict,'response-local raw Driver reference missing; no glob/latest fallback')
        ref=ev['raw_result_reference'];path=Path(ref['path'])
        need(path.is_absolute() and path.parent.resolve()==(self.assets/'state-a01/native-session/army-query-history-results').resolve()
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
        return observation,{'snapshot':sref,'strength':actual}
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
    def current_lock(self,o):
        r=o['route'];m=o['movement']
        need(len(r)>=2 and r[0]!=r[-1] and m.get('status')=='available','current original route is not multi-hop/available')
        p=self.v.amount(m.get('normalized_edge_progress'),'actual progress');c=self.v.amount(m.get('loaded_movement_lock_cutoff'),'actual cutoff')
        rem=self.v.amount(m.get('first_route_edge_remaining_duration'),'first-edge remaining')
        need(rem>=0,'remaining duration negative')
        return {'eligible_at_or_above_cutoff':p>=c,'strict_native_locked':p>c,'relation':'greater' if p>c else 'equal' if p==c else 'below',
            'progress_raw':p,'cutoff_raw':c,'first_edge_remaining_q100000':rem,'front':r[0],'tail':r[-1],
            'first_edge_day_budget':(rem+99999)//100000+2}
    def preview(self,o,source_pin):
        source=Path(source_pin);envelope=load(source)
        need(envelope.get('machine_id')==self.machine and envelope.get('is_error') is False,'Root legal preview envelope not actual same machine')
        original=envelope.get('body') or {};route=original.get('route_preview') or {}
        need(original.get('accepted') is True and route.get('status')=='available'
             and route.get('army_id')==self.binding['army_id'],'Root legal preview not available for selected Army')
        target=route.get('target_province_id');need(type(target) is int and target>0,'legal preview target missing')
        # The target comes from the supplied actual legal preview, never a
        # guessed Province ID. Query again to bind legality to this fresh frame.
        row,_,ref=self.request('fresh-legal-preview','ck3_execute_step',{'step':f"preview-move-army-{self.binding['army_id']}-to-{target}",'expected_revision':o['snapshot']['revision']})
        path=self.v.preview_path(row['body'],o,target)
        return target,path,ref,pin(source)
    def baseline(self):
        need(not (self.case/'baseline.actual.json').exists(),'baseline already complete; never repeat normal initial Move')
        o,refs=self.frame('baseline');self.v.stationary(o)
        if self.args.preview_response is None:
            return {'status':'BASELINE-READONLY; NEED_ROOT_LEGAL_PREVIEW','baseline':refs,'binding':self.binding}
        target,route,preview,source=self.preview(o,self.args.preview_response)
        need(len(route)>=2 and route[0]!=route[-1],'new lawful initial Move must be multi-hop')
        ack=self.action('initial-move','ck3_move_army',{'army_id':self.binding['army_id'],'target_province_id':target,
            'expected_revision':o['snapshot']['revision']},{'before':refs,'preview':preview,'preview_source':source,'target':target,'expected_route':route})
        after,post=self.frame('initial-post');self.v.same_paused_applied(o,after)
        need(after['route']==route,'normal new Move has not independently applied expected route; no resend')
        session=write_new(self.case/'session.actual.json',{'machine_id':self.machine,'pid':self.binding['pid'],
            'process_create_time_100ns':self.binding['process_create_time_100ns'],'runtime_proof':self.proof_pin})
        result={**self.meta,'status':'NEW-NORMAL-MOVE-INDEPENDENTLY-OBSERVED','binding':self.binding,
            'baseline':refs,'new_move_post':post,'initial_target':target,'initial_preview':preview,
            'initial_move_request':ack['request'],'initial_move_response':ack['response'],'session_receipt':pin(session),
            'original_province':after['province'],'original_route':route,'starting_date_raw':after['date']}
        write_new(self.case/'baseline.actual.json',result);return result
    def base(self):
        b=load(self.case/'baseline.actual.json',1024*1024);need(b['binding']==self.binding and b['case']==self.args.card,'baseline not this session/case')
        return b
    def day(self,o):
        start=o['date'];target=start+24
        key='day-'+str(start);self.claim(key,{'starting_date_raw':start,'target_date_raw':target})
        step=f"research-arm-tactical-daily-sentinel-v1-{start}-to-{target}-speed-5-mode-terminal-a-1-{self.binding['army_id']}"
        row,_,_=self.request('arm-one-day','ck3_execute_step',{'step':step,'expected_revision':o['snapshot']['revision']})
        armed=row['body'].get('tactical_daily_sentinel') or {};need(armed.get('state')=='armed','sentinel arm not actually armed; no repeat')
        s,_=self.snap('before-resume');need(s['date_raw']==start,'date changed before one resume')
        self.request('resume-once','ck3_execute_step',{'step':'resume-map','expected_revision':s['revision']})
        deadline=time.monotonic()+60
        for _ in range(60):
            time.sleep(.5);s,_=self.snap('wait-paused',paused=False)
            if s.get('paused') is True:break
            need(time.monotonic()<deadline,'no independently observed pause within60s')
        need(s.get('paused') is True and s['date_raw']==target,'one exact +24 natural day not observed')
        row,_,ref=self.request('daily-status','ck3_execute_step',{'step':'research-query-tactical-daily-sentinel-v1','expected_revision':s['revision']})
        clock=row['body'].get('tactical_daily_sentinel') or {};reasons=clock.get('trigger_reasons') or []
        need(clock.get('generation')==armed.get('generation') and clock.get('state')=='triggered'
             and clock.get('starting_date_raw')==start and clock.get('target_date_raw')==target and clock.get('trigger_date_raw')==target
             and clock.get('completed_daily_ticks')==1 and clock.get('overshoot_days')==0 and clock.get('abnormal') is False
             and clock.get('pause_observed') is True and clock.get('pause_wrapper_called') is True
             and 'date_deadline' in reasons and set(reasons)<={'date_deadline','army_position_changed','route_target_changed'},
             'actual daily stop generation/date/pause/reasons mismatch')
        write_new(self.case/(key+'.complete.actual.json'),{**self.meta,'clock_response':ref,'starting_date_raw':start,'date_raw':target})
        return self.frame('after-day')
    def lock_wait(self):
        b=self.base();o,refs=self.frame('lock-start')
        for day in range(self.args.max_days+1):
            need(o['province']==b['original_province'] and o['route']==b['original_route'],'original first edge/route ended before lock capture')
            lock=self.current_lock(o)
            if lock['eligible_at_or_above_cutoff']:
                result={**self.meta,'status':'CURRENT-PROGRESS-AT-OR-ABOVE-CUTOFF','binding':self.binding,
                    'locked':refs,'actual':lock,'days_advanced_this_stage':day,
                    'equal_boundary_is_not_strict_locked_credit':lock['relation']=='equal'}
                write_new(self.case/'lock.admission.actual.json',result);return result
            need(day<self.args.max_days,'finite lock search days exhausted; no automatic new route')
            o,refs=self.day(o)
    def halt_once(self):
        need(self.args.card=='R12','Halt-once belongs to independent R12 case')
        b=self.base();o,refs=self.frame('before-halt');lock=self.current_lock(o)
        need(lock['eligible_at_or_above_cutoff'] and o['province']==b['original_province'] and o['route']==b['original_route'],
             'fresh actual route/progress no longer at-or-above cutoff')
        return self.action('halt','ck3_execute_step',{'step':f"halt-army-{self.binding['army_id']}",'expected_revision':o['snapshot']['revision']},
            {'locked':refs,'actual':lock,'original_route':o['route'],'original_province':o['province'],'locked_date':o['date']})
    def move_alt_once(self):
        need(self.args.card=='R13' and self.args.preview_response is not None,'R13 needs supplied actual Root legal alternate preview')
        b=self.base();o,refs=self.frame('before-alt');lock=self.current_lock(o)
        need(lock['eligible_at_or_above_cutoff'] and o['province']==b['original_province'] and o['route']==b['original_route'],
             'independent R13 normal initial first edge no longer at-or-above cutoff')
        alt,route,preview,source=self.preview(o,self.args.preview_response)
        need(alt not in {o['province'],lock['front'],lock['tail']} and route[0]==lock['front']
             and lock['tail'] not in route[1:] and route[1:]!=o['route'][1:],
             'fresh legal alternate must preserve first and genuinely replace suffix; no old-tail shortcut')
        return self.action('alt-move','ck3_move_army',{'army_id':self.binding['army_id'],'target_province_id':alt,'expected_revision':o['snapshot']['revision']},
            {'locked':refs,'actual':lock,'original_route':o['route'],'original_province':o['province'],'locked_date':o['date'],
             'alternate_target':alt,'alternate_preview':preview,'preview_source':source,'expected_route':route})
    def readback(self,kind):
        action=self.action_original(kind);lock=action['actual']
        post_path=self.case/(kind+'.post.actual.json')
        if post_path.exists():
            post=load(post_path,1024*1024);o,refs=self.frame('continue-readback')
        else:
            o,refs=self.frame('independent-post')
            expect=[lock['front']] if kind=='halt' else action['expected_route']
            for _ in range(8):
                if o['route']==expect:break
                need(o['date']==action['locked_date'] and o['province']==action['original_province'],
                     'immediate action consequence was not captured before natural advance')
                time.sleep(.2);o,refs=self.frame('post-async-readonly')
            need(o['route']==expect and o['date']==action['locked_date'] and o['province']==action['original_province'],
                 'actual route suffix consequence not independently observed; never resend action')
            before=self.v.frame(load(action['locked']['snapshot']['path'])['body'],load(action['locked']['strength']['path']),self.binding)
            self.v.same_paused_applied(before,o)
            need(self.v.amount(o['movement'].get('normalized_edge_progress'),'post progress')==lock['progress_raw']
                 and self.v.amount(o['movement'].get('loaded_movement_lock_cutoff'),'post cutoff')==lock['cutoff_raw'],
                 'first-edge progress/cutoff not retained')
            post={**self.meta,'post':refs,'locked_date':action['locked_date'],'actual':lock}
            write_new(post_path,post)
        first_path=self.case/(kind+'.first-arrival.actual.json');first=load(first_path,1024*1024) if first_path.exists() else None
        limit=min(self.args.max_days,lock['first_edge_day_budget']) if kind=='halt' else self.args.max_days
        for day in range(limit+1):
            elapsed=o['date']-action['locked_date'];need(elapsed>=0 and elapsed%24==0,'readback crossed non-natural date interval')
            if o['province']==lock['front'] and not first:
                first={**self.meta,'frame':refs,'date_raw':o['date'],'province':o['province']}
                write_new(first_path,first)
            arrived=(o['province']==lock['front'] and o['route']==[]) if kind=='halt' else (o['province']==action['alternate_target'] and o['route']==[])
            if arrived:
                self.v.stationary(o)
                need(first is not None,'actual original front was never observed; no invented intermediate arrival')
                need(first['date_raw']-action['locked_date']<=lock['first_edge_day_budget']*24,'first arrival beyond actual first-edge remaining+2')
                result={**self.meta,'status':'ACTUAL-ARRIVAL-INDEPENDENTLY-OBSERVED','binding':self.binding,
                    'post':post['post'],'first_arrival':first['frame'],'arrival':refs,'elapsed_natural_days':elapsed//24,
                    'actual_destination':o['province'],'strict_locked':lock['strict_native_locked']}
                write_new(self.case/(kind+'.arrival.actual.json'),result);return result
            need(day<limit,'finite readback day budget exhausted; preserved readback may continue only via new explicit attempt')
            if kind=='halt':need(elapsed<lock['first_edge_day_budget']*24,'Halt first-edge+2 bound reached')
            o,refs=self.day(o)
    def report(self):
        b=self.base();kind='halt' if self.args.card=='R12' else 'alt-move';a=self.action_original(kind)
        final=load(self.case/(kind+'.arrival.actual.json'),1024*1024)
        manifest={'machine_id':self.machine,'case':self.args.card,'case_id':self.args.case_id,'binding':self.binding,
            'owned_evidence_roots':[str(self.assets)],'initial_move_count':1,'action_count':1,'maximum_natural_days':self.args.max_days,
            'session_receipt':b['session_receipt'],'baseline':b['baseline'],'new_move_post':b['new_move_post'],
            'locked':a['locked'],'post':final['post'],'arrival':final['arrival'],'initial_target':b['initial_target'],
            'initial_preview':b['initial_preview'],'initial_move_request':b['initial_move_request'],'initial_move_response':b['initial_move_response'],
            'action_request':a['request'],'action_response':a['response'],'daily_clock_results':[]}
        days=sorted((load(p,1024*1024) for p in self.case.glob('day-*.complete.actual.json')),key=lambda v:v['starting_date_raw'])
        manifest['daily_clock_results']=[v['clock_response'] for v in days]
        if self.args.card=='R13':manifest.update(first_arrival=final['first_arrival'],alternate_target=a['alternate_target'],alternate_preview=a['alternate_preview'])
        mpath=write_new(self.attempt/'case.manifest.actual.json',manifest)
        if not a['actual']['strict_native_locked']:
            return {'status':'ACTUAL-EQUAL-BOUNDARY-CASE; NOT-STRICT-LOCKED-CARD','manifest':pin(mpath),'actual':a['actual'],
                'strict_portable_verifier_not_relaxed':True,'live_card_credit':False}
        result=self.v.audit_manifest(manifest,base_dir=self.case)
        return {**self.meta,'status':result['status'],'manifest':pin(mpath),'portable_result':result,'human_video_signoff':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=('baseline','lock-wait','Halt-once','postHalt-readback','Move-alt-once','postMove-readback','report'))
    p.add_argument('--repo',type=Path,required=True);p.add_argument('--context',type=Path,required=True)
    p.add_argument('--runtime-proof',type=Path,required=True);p.add_argument('--runtime-proof-sha256',required=True)
    p.add_argument('--request-helper',type=Path,required=True);p.add_argument('--request-helper-sha256',required=True)
    p.add_argument('--case-id',required=True);p.add_argument('--card',choices=('R12','R13'),required=True);p.add_argument('--attempt',required=True)
    p.add_argument('--deadline-utc',required=True,help='Root original admitted deadline; fixed across this case, never extended by helper')
    p.add_argument('--army-id',type=int,default=18);p.add_argument('--max-days',type=int,default=12)
    p.add_argument('--preview-response',type=Path,help='Actual same-run Root legal preview; target is taken from its native body, never guessed')
    args=p.parse_args();need(1<=args.max_days<=30,'finite stage natural-day bound1..30')
    live=None
    try:
        live=Live(args)
        functions={'baseline':live.baseline,'lock-wait':live.lock_wait,'Halt-once':live.halt_once,
            'postHalt-readback':lambda:live.readback('halt'),'Move-alt-once':live.move_alt_once,
            'postMove-readback':lambda:live.readback('alt-move'),'report':live.report}
        result=functions[args.stage]();path=write_new(live.attempt/'RESULT.actual.json',{**live.meta,'result':result})
        print(json.dumps({'created':str(path),'stage':args.stage,'helper':live.meta['helper'],'runtime_proof':live.proof_pin}));return 0
    except BaseException as error:
        if live is not None:
            write_new(live.attempt/'FAILURE.actual.json',{**live.meta,'error_type':type(error).__name__,'error':str(error)[:4000],
                'pending_original_response':live.pending,'last_actual_date_raw':live.last.get('date_raw') if live.last else None,
                'paused_independently_observed':bool(live.last and live.last.get('paused')),
                'replay_forbidden':True,'Root_recovery':'Inspect exact original action response and fresh owned state; do not repeat claimed Move/Halt/Arm/resume.'})
        raise
if __name__=='__main__':raise SystemExit(main())
