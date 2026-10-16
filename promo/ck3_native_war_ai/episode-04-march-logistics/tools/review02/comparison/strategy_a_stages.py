"""A-only phase adapter over the existing SHA-pinned Root file relay.

Import/help are offline. Only a Root-invoked explicit phase uses that relay.
No SDK client, recorder, game launch, normal-save reader, or phase chaining.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path


def load_module(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def load_dependencies(args):
    relay=args.relay_source.resolve();raw=relay.read_bytes()
    if len(raw)>65536 or hashlib.sha256(raw).hexdigest()!=args.relay_sha256:
        raise ValueError('existing reviewed relay source pin differs')
    h=load_module(relay,'A_existing_root_relay')
    root=args.consumer_root.resolve();pins=h.load(args.consumer_manifest,1024*1024)
    for name in ('r10_compare.py','r10.schema.json','strategy_a.py','strategy_a_route_inputs.py'):
        p=root/name;actual=h.pin(p)
        h.need(actual['bytes']==pins[name]['bytes'] and actual['sha256']==pins[name]['sha256'],
               'existing consumer pin differs: '+name)
    sys.path.insert(0,str(root))
    c=load_module(root/'r10_compare.py','r10_compare');sys.modules['r10_compare']=c
    a=load_module(root/'strategy_a.py','strategy_a');sys.modules['strategy_a']=a
    ri=load_module(root/'strategy_a_route_inputs.py','A_existing_route_inputs')
    return h,c,a,ri


def make_live_class(h,c,a,ri):
    class AStages(h.Live):
        # request/snapshot/once claim/action/late-original ACK/process-time are
        # inherited unchanged. Only A binding and business phase glue are new.
        def __init__(self,args):
            self.args=args;self.repo=args.repo.resolve();self.process_probe=h.process_time
            self.plan=h.load(args.plan,1024*1024);self.runtime=h.load(args.runtime,1024*1024)
            c.schema_check(self.runtime,'runtime');self.e=c.Evidence(args.evidence_root, **c.evidence_file_options(vars(args),
                source_head=self.runtime['source_head'], machine_ids=[self.runtime['machine_id']]))
            self.e.all_pins(self.runtime);self.features=h.load(args.features_binding,1024*1024)
            self.e.bound(self.features)
            h.need(self.plan['status']=='frozen' and self.plan['strategies']['A']['mode']=='whole-direct',
                   'existing A plan must be frozen whole-direct')
            h.need(args.loaded_save_sha256==self.plan['normal_save']['sha256'],'same normal T0 SHA required')
            self.machine=self.runtime['machine_id'];self.context_path=args.context.resolve()
            self.c=h.load(self.context_path,1024*1024);identity=self.c['identity']
            source=self.plan['build']['source_head']
            head=subprocess.run(['git','-C',str(self.repo),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
            h.need(head==source==self.runtime['source_head']==self.c['source_head'],'frozen source differs')
            h.need(self.c['machine_id']==identity['machine_id']==self.machine and identity['mod_key']=='vanilla',
                   'normal owned allocation machine differs')
            self.assets=self.context_path.parent;self.run=self.assets/identity['run_id']
            h.need(self.run.is_dir(),'Root allocated new run absent')
            self.deadline=datetime.fromisoformat(args.deadline_utc.replace('Z','+00:00'))
            guards=load_module(Path(__file__).resolve().parents[1]/'runtime_binding.py','A_explicit_runtime_guard')
            binding_path=getattr(args,'live_binding',None)
            if binding_path is not None:
                h.need(guards.current_machine_id(self.repo)==self.machine,'actual execution machine differs')
            self.live_operation_guard=guards.optional_guard(binding_path,getattr(args,'live_binding_sha256',None),
                context=self.c,runtime=guards.arm_runtime(self.runtime),scene_root=self.assets,
                source_head=source,machine_id=self.machine,run_id=identity['run_id'],
                max_runtime_total_bytes=args.max_runtime_total_bytes,deadline_utc=args.deadline_utc,
                normal_save_sha256=args.loaded_save_sha256)
            if self.live_operation_guard is None:
                h.need(self.deadline.tzinfo is not None and self.deadline<=datetime.fromisoformat('2026-10-16T07:45:01.597000+00:00'),
                       'new deadline requires an exact explicit live binding; historical deadline cannot be extended')
            h.need(self.deadline.tzinfo is not None and datetime.now(timezone.utc)<self.deadline,
                   'operation deadline reached; no new live stage')
            h.need(0<=args.army_id<=2**31-1 and 0<=args.native_carmy_id<=2**31-1,
                   'public CUnit and separately observed native CArmy permit zero')
            self.binding={'pid':self.runtime['pid'],'process_create_time_100ns':self.runtime['process_create_time_100ns'],
                'generation':self.runtime['connection_generation'],'actor':self.runtime['player_character_id'],
                'episode':self.runtime['episode'],'army_id':args.army_id,'native_carmy_id':args.native_carmy_id}
            self.proof_pin=h.pin(self.e.root/self.runtime['source_proof']['path'])
            if self.live_operation_guard:
                proof=h.load(self.proof_pin['path'],1024*1024)
                h.need(guards.proof_runtime(proof)==self.live_operation_guard.runtime
                       and proof.get('machine_id')==self.machine and proof.get('run_id')==identity['run_id']
                       and proof.get('source_head')==source,'source proof differs from the new live operation')
            self.helper_pin=h.pin(args.request_helper,65536)
            h.need(self.helper_pin['sha256']==args.request_helper_sha256,'Root request helper changed')
            self.transport=load_module(args.request_helper,'A_owned_existing_request_relay')
            h.need(Path(self.transport.RUN).resolve()==self.run.resolve()
                   and Path(self.transport.ASSETS).resolve()==self.assets.resolve()
                   and self.transport.CONTEXT['identity']==identity,'existing relay is not allocated new A run')
            self.v=load_module(self.repo/h.VERIFY_REL,'A_existing_frame_reader')
            import re
            h.need(all(re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,47}',s) for s in (args.case_id,args.attempt)),
                   'explicit unique case/attempt required')
            self.ledger=self.assets/'r10-a-stages-a03';self.case=self.ledger/args.case_id
            self.case.mkdir(parents=True,exist_ok=True);self.attempt=self.case/args.attempt;self.attempt.mkdir(exist_ok=False)
            self.pending=False;self.serial=0;self.last=None
            self.meta={'machine_id':self.machine,'source_head':source,'at_utc':h.utc(),'run_id':identity['run_id'],
                'case_id':args.case_id,'case':'R10-A','stage':args.stage,'helper':h.pin(Path(__file__)),
                'existing_relay':h.pin(args.relay_source),'runtime_proof':self.proof_pin,
                'request_helper':self.helper_pin,'deadline_utc':self.deadline.isoformat(),
                'phases_chained':False,'SDK_connection_created':False,'new_run_capacity_granted_by_adapter':False}
            if self.live_operation_guard:
                self.meta.update(live_operation_binding=self.live_operation_guard.pin,
                                 capacity_admission=self.live_operation_guard.capacity_pin)
            budget=c.runtime_total_budget(guards.runtime_options(vars(args),self.live_operation_guard),scene_root=self.assets,source_head=source,
                machine_id=self.machine,deadline_utc=self.deadline.isoformat())
            budget.bind_live(self,base_module=h,raw_file_max=args.max_evidence_file_bytes)
            saved=self.case/'binding.actual.json'
            if saved.exists():
                prior=h.load(saved,1024*1024)
                h.need(prior.get('live_operation_binding')==self.meta.get('live_operation_binding'),
                       'case operation binding changed; cannot adopt old/different case')
                h.need(prior['deadline_utc']==self.meta['deadline_utc'],'case deadline changed')
                h.need(all(prior['binding'][k]==v for k,v in self.binding.items() if k!='native_carmy_id'),
                       'case crossed owned runtime')
                self.binding=prior['binding']
            else:h.write_new(saved,{**self.meta,'binding':self.binding})
            self.check_process()
            h.write_new(self.attempt/'START.actual.json',{**self.meta,'binding':self.binding})

        def request(self,*values,**kwargs):
            if getattr(self,'live_operation_guard',None):self.live_operation_guard.check()
            return super().request(*values,**kwargs)

        def used_bytes(self):
            # Include the full query sidecars absent from the older relay meter.
            total=super().used_bytes()
            for directory in (self.assets/'state-a01/native-session/army-query-history-results',):
                if directory.exists():total+=sum(p.stat().st_size for p in directory.iterdir() if p.is_file())
            return total

        def relative_pin(self,pin):
            p=Path(pin['path']).resolve();actual=h.pin(p)
            h.need(actual['bytes']==pin['bytes'] and actual['sha256']==pin['sha256'],'original pin changed')
            h.need(p.is_relative_to(self.e.root),'all small evidence must be within explicit evidence-root')
            return {'path':p.relative_to(self.e.root).as_posix(),'bytes':pin['bytes'],'sha256':pin['sha256']}

        def endpoint(self,name):
            _,refs=super().frame(name)  # Existing scoped raw-result reference, no summary/latest fallback.
            s=c.frame(self.e.json(self.relative_pin(refs['snapshot'])),self.runtime)
            delta=s['date_raw']-self.plan['t0_raw'];h.need(delta>=0 and delta%24==0,'not an actual T0 natural day')
            cmd,_,cmdref=self.request(name+'-commander','ck3_query_army_commander_candidates_v1',
                {'army_id':self.binding['army_id'],'expected_revision':s['revision']})
            b=cmd['body'];cc=b.get('army_commander_candidates') or {};current=cc.get('current_commander') or {}
            h.need(all(b.get('queried_'+k)==s[k] for k in ('snapshot_id','revision','native_revision'))
                   and cc.get('date_raw')==s['date_raw'] and cc.get('army_id')==self.binding['army_id']
                   and cc.get('owner_character_id')==self.binding['actor'] and current.get('status')=='available'
                   and type(current.get('character_id')) is int,'current commander source/frame unavailable; never fill zero')
            ep={'day':delta//24,'snapshot':self.relative_pin(refs['snapshot']),
                'army_result':self.relative_pin(refs['strength']),'strategy_army_ids':[self.binding['army_id']],
                'commander':{'source':self.relative_pin(cmdref),'pointer':'/body/army_commander_candidates/current_commander/character_id'},
                'loaded_features':self.features}
            a._whole(ep,self.plan,self.e,self.runtime,self.binding['army_id'])
            return ep

        def fresh_preview(self,ep):
            s=c.frame(self.e.json(ep['snapshot']),self.runtime)
            _,_,ref=self.request('fresh-direct-preview','ck3_execute_step',
                {'step':f'preview-move-army-{self.binding["army_id"]}-to-{self.plan["goal_province_id"]}',
                 'expected_revision':s['revision']})
            pin=self.relative_pin(ref);a._preview(pin,ep,self.plan,self.e,self.runtime);return pin

        def state(self):
            h.need(self.args.state is not None,'explicit prior STATE file required; no latest/glob')
            state=h.load(self.args.state,1024*1024)
            h.need(state['plan']==self.plan and state['runtime']==self.runtime
                   and state['army_id']==self.binding['army_id'],'prior A state source/runtime differs')
            return state

        def save_state(self,state,name='STATE.actual.json'):
            return h.write_new(self.attempt/name,state)

        def baseline(self):
            h.need(not (self.case/'initial-move.once.claim.json').exists(),'Move already claimed; baseline cannot reset case')
            ep=self.endpoint('baseline');h.need(ep['day']==0,'A baseline is not T0')
            preview=self.fresh_preview(ep)
            state=a.admit(self.plan,self.runtime,self.args.loaded_save_sha256,ep,preview,self.e)
            path=self.save_state(state)
            return {'state':h.pin(path),'decision':ri.next_decision(state,self.e,preview),'Move_submitted':False}

        def move_once(self):
            prior=self.state();h.need(not prior['days'] and prior['move_postcondition'] is None,'not before initial Move')
            ep=self.endpoint('before-one-Move');preview=self.fresh_preview(ep)
            state=a.admit(self.plan,self.runtime,self.args.loaded_save_sha256,ep,preview,self.e)
            state_pin=h.pin(self.save_state(state,'STATE.before-move.actual.json'))
            call=state['proposed_call']
            ack=self.action('initial-move',call['tool'],call['arguments'],{'before_state':state_pin,'expected_route':state['route']})
            return {'ack':ack,'state_before_Move':state_pin,'postcondition_verified':False,'next_phase':'Move-post'}

        def move_post(self):
            state=self.state();ack=self.action_original('initial-move')
            h.need(h.pin(self.args.state)==ack['before_state'],'Move-post must consume exact pre-Move state from claim')
            for n in range(8):
                s,_=self.snap('asynchronous-Move-post')
                row=next(x for x in s['player_armies'] if x['army_id']==self.binding['army_id'])
                if row.get('route_province_ids')==state['route'] and row.get('move_target_province_id')==self.plan['goal_province_id']:
                    break
                time.sleep(.2)
            ep=self.endpoint('independent-Move-post');state=a.observe_move(state,ep,self.e)
            return {'state':h.pin(self.save_state(state)),'independent_Move_post':ep,'Move_reissued':False}

        def exact_day(self,state):
            before=self.endpoint('one-day-before');s=c.frame(self.e.json(before['snapshot']),self.runtime)
            h.need(before['day']==len(state['days']),'original natural-day budget changed; no reset')
            current,_=a._whole(before,self.plan,self.e,self.runtime,self.binding['army_id'])
            h.need(current==state['actual'],'current complete Army changed; ordinary policy must inspect')
            if s.get('speed')!=5:
                self.request('set-existing-speed5','ck3_execute_step',{'step':'set-speed-5','expected_revision':s['revision']})
                before=self.endpoint('speed5-independent-before');s=c.frame(self.e.json(before['snapshot']),self.runtime)
                h.need(s.get('speed')==5,'actual speed5 not observed')
                h.need(before['day']==len(state['days']) and
                       a._whole(before,self.plan,self.e,self.runtime,self.binding['army_id'])[0]==state['actual'],
                       'set-speed crossed date or changed complete Army; do not arm')
            start=s['date_raw'];target=start+24
            self.claim('day-'+str(start),{'starting_date_raw':start,'target_date_raw':target,'before':before})
            step=f'research-arm-tactical-daily-sentinel-v1-{start}-to-{target}-speed-5-mode-terminal-a-0'
            arm,_,_=self.request('arm-one-date-day','ck3_execute_step',{'step':step,'expected_revision':s['revision']})
            armed=arm['body'].get('tactical_daily_sentinel') or {};h.need(armed.get('state')=='armed','Arm unknown; no retry')
            self.request('resume-once','ck3_execute_step',{'step':'resume-map','expected_revision':None})
            for _ in range(60):
                time.sleep(.15);stop,_=self.snap('date-only-stop',paused=False)
                if stop.get('paused') is True and stop['date_raw']>start:break
            h.need(stop.get('paused') is True and stop['date_raw']==target,'exact native +24 not independently paused')
            status,_,ref=self.request('date-only-status','ck3_execute_step',
                {'step':'research-query-tactical-daily-sentinel-v1','expected_revision':None})
            clock=status['body'].get('tactical_daily_sentinel') or {}
            h.need(clock.get('generation')==armed.get('generation'),'Arm/Status generation differs')
            # A new post-status frame avoids the demonstrated stale-public-revision failure.
            after=self.endpoint('post-status-independent-full-DATA')
            row={'day':after['day'],'clock_source':self.relative_pin(ref),
                 'paused_snapshot':after['snapshot'],'strategy_army_ids':after['strategy_army_ids']}
            state=a.update(state,row,after,self.e)
            h.write_new(self.case/f'day-{start}.complete.actual.json',{**self.meta,'before':before,'day':row,'after':after})
            self.save_state(state,'STATE.day-'+str(after['day'])+'.actual.json')
            return state

        def advance(self):
            state=self.state();h.need(state['move_postcondition'] is not None,'independent Move-post required')
            h.need(state['first_arrival_day'] is None,'arrival reached; use separate post phase, no automatic continuation')
            for _ in range(self.args.days):
                if len(state['days'])==90 or state['first_arrival_day'] is not None:break
                if a.report(state)['action_status']=='needs_current_state_decision':break
                state=self.exact_day(state)
            return {'state':h.pin(self.save_state(state)),'report':a.report(state),'Move_submitted':False}

        def common_horizon_anchor(self,state):
            h.need(self.plan.get('status')=='frozen'
                   and self.plan.get('follow_after_arrival_to_day90') is True
                   and self.plan.get('post_arrival_policy')=='hold-arrival-position-until-day90',
                   'common horizon requires the prespecified hold-arrival-position-until-day90 policy')
            frozen=datetime.fromisoformat(self.plan['frozen_at_utc'].replace('Z','+00:00'))
            started=datetime.fromisoformat(self.runtime['started_at_utc'].replace('Z','+00:00'))
            h.need(frozen.tzinfo is not None and started.tzinfo is not None and frozen<started,
                   'hold policy was not frozen before this cold session')
            day=len(state['days']);first=state['first_arrival_day']
            h.need(type(first) is int and 1<=first<=day<90 and state['move_postcondition'] is not None,
                   'common horizon needs an actual arrival before absolute day90')
            endpoints=[ep for ep in state['observations'] if ep['day']==first]
            h.need(len(endpoints)==1 and state['observations'][-1]['day']==day,
                   'original arrival/latest endpoint absent or ambiguous')
            arrival,_=a._whole(endpoints[0],self.plan,self.e,self.runtime,self.binding['army_id'])
            current,_=a._whole(state['observations'][-1],self.plan,self.e,self.runtime,self.binding['army_id'])
            h.need(arrival==state['arrival_actual'] and current==state['actual']
                   and c.arrived(arrival,self.plan) and c.arrived(current,self.plan),
                   'actual arrival/current hold position differs from the preserved endpoints')
            clock=c.clock_days({'runtime':self.runtime,'days':state['days']},self.plan,self.e)
            h.need(clock['first_arrival']==first,'first arrival differs from original daily scan')
            return first,state['last_not_arrived_day'],arrival,endpoints[0]

        def hold_signature(self,actual,endpoint):
            # Current soldiers, stock, rates and wallet may change naturally.
            # Preserve cached ArRg/full DATA identities and maxima independently.
            query=c.body(self.e.json(endpoint['army_result']))
            cached=tuple((unit['army_id'],tuple((r['army_regiment_id'],r['maximum_soldiers'])
                         for r in unit['regiment_strengths'])) for unit in query['army_strengths'])
            records=[]
            for row in query['army_strengths'][0]['regiment_replenishment_records_v1']:
                items=[]
                for rec in row['records']:
                    values=tuple(rec.get(k) for k in ('record_index','persistent_regiment_id','chunk_index','maximum_soldiers'))
                    h.need(type(values[1]) is int and -(1<<31)<=values[1]<(1<<31),
                           'hold requires signed32 persistent FullID')
                    h.need(all(type(values[n]) is int and 0<=values[n]<(1<<31) for n in (0,2,3)),
                           'hold requires complete DATA index/slot/max')
                    items.append(values+(rec.get('chunk_army_regiment_id'),))
                records.append((row['army_regiment_id'],row['native_data_record_count'],tuple(items)))
            maxima=tuple((u['army_id'],u['maximum_soldiers']) for u in actual['units'])
            return actual['player_character_id'],actual['commander_id'],cached,tuple(records),maxima

        def advance_common_horizon(self):
            state=self.state();first,last_not,arrival,arrival_ep=self.common_horizon_anchor(state)
            import copy
            anchor=copy.deepcopy((first,last_not,arrival,arrival_ep))
            signature=self.hold_signature(arrival,arrival_ep)
            h.need(self.hold_signature(state['actual'],state['observations'][-1])==signature,'hold-arrival commander/cohort/DATA/max changed')
            for _ in range(self.args.days):
                if len(state['days'])==90:break
                state=self.exact_day(state)  # Existing global once Arm/Resume and full exact-day consumer.
                try:
                    h.need((state['first_arrival_day'],state['last_not_arrived_day'],state['arrival_actual'],
                            next(ep for ep in state['observations'] if ep['day']==first))==anchor,
                           'first arrival or its original endpoint was rewritten')
                    h.need(c.arrived(state['actual'],self.plan),'hold-arrival position interrupted; ordinary policy must inspect')
                    h.need(self.hold_signature(state['actual'],state['observations'][-1])==signature,'hold-arrival commander/cohort/DATA/max changed')
                except Exception as error:
                    h.write_new(self.attempt/'HOLD-INTERRUPTION.actual.json',{**self.meta,
                        'error':str(error),'actual_day_executed':True,'date_raw':state['actual']['date_raw'],
                        'actual_state':h.pin(self.attempt/f"STATE.day-{len(state['days'])}.actual.json"),
                        'original_day_complete':h.pin(self.case/f"day-{state['actual']['date_raw']-24}.complete.actual.json"),
                        'actual_endpoint':state['observations'][-1],'original_arrival_endpoint':arrival_ep,
                        'Arm_Resume_Move_reissued':False,'ordinary_policy_inspection_required':True})
                    raise
            return {'state':h.pin(self.save_state(state)),'report':a.report(state),'Move_submitted':False,
                    'common_horizon_policy':'hold-arrival-position-until-day90',
                    'first_arrival_preserved':True,'absolute_D90_reached':len(state['days'])==90}

        def post(self):
            state=self.state();ep=self.endpoint('arrival-or-bound-independent-post')
            actual,_=a._whole(ep,self.plan,self.e,self.runtime,self.binding['army_id'])
            h.need(ep['day']==len(state['days']),'post is not same terminal natural day')
            if state['first_arrival_day'] is not None:h.need(c.arrived(actual,self.plan),'actual post no longer meets frozen arrival definition')
            else:h.need(len(state['days'])==90,'early STOP is neither arrival nor D90 censor')
            return {'report':a.report(state),'independent_post':ep,'independent_actual':actual,
                    'post_arrival_days_added':0,'actual_fees':None,'full_ABC_qualification':False}
    return AStages


def parser():
    p=argparse.ArgumentParser(description=__doc__,fromfile_prefix_chars='@')
    p.add_argument('stage',choices=('baseline','Move-once','Move-post','advance','advance-common-horizon','post'))
    for name in ('repo','relay-source','consumer-root','consumer-manifest','plan','runtime','features-binding',
                 'evidence-root','context','request-helper'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('relay-sha256','request-helper-sha256','loaded-save-sha256','case-id','attempt','deadline-utc'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--army-id',type=int,required=True);p.add_argument('--native-carmy-id',type=int,required=True)
    p.add_argument('--max-runtime-total-bytes',type=int,default=512*1024*1024)
    p.add_argument('--runtime-capacity-admission',nargs=2,metavar=('PATH','SHA256'))
    p.add_argument('--live-binding',type=Path);p.add_argument('--live-binding-sha256')
    p.add_argument('--max-evidence-file-bytes',type=int,choices=(16777216,33554432),default=16777216)
    p.add_argument('--evidence-capacity-admission',nargs=2,action='append',default=[],metavar=('PATH','SHA256'))
    p.add_argument('--state',type=Path)
    p.add_argument('--days',type=int,default=1)
    return p


def main():
    args=parser().parse_args()
    if not 1<=args.days<=30:raise ValueError('existing bounded stage range is1..30; absolute total remains90')
    h,c,a,ri=load_dependencies(args);live=None
    try:
        live=make_live_class(h,c,a,ri)(args)
        fn={'baseline':live.baseline,'Move-once':live.move_once,'Move-post':live.move_post,'advance':live.advance,'advance-common-horizon':live.advance_common_horizon,'post':live.post}[args.stage]
        result=fn();path=h.write_new(live.attempt/'RESULT.actual.json',{**live.meta,'result':result})
        print(json.dumps({'phase':args.stage,'result':str(path),'phases_chained':False}));return 0
    except BaseException as error:
        if live is not None:h.write_new(live.attempt/'FAILURE.actual.json',{**live.meta,'error':str(error)[:4000],
            'pending_original_response':live.pending,'unknown_action_retry':False,'new_request_retry':False})
        raise

if __name__=='__main__':raise SystemExit(main())
