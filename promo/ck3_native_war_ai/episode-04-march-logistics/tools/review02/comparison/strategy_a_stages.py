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
            c.schema_check(self.runtime,'runtime');self.e=c.Evidence(args.evidence_root)
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
            h.need(self.deadline.tzinfo is not None and self.deadline<=datetime.fromisoformat('2026-10-16T07:45:01.597000+00:00'),
                   'original admitted deadline cannot be extended')
            h.need(0<=args.army_id<=2**31-1 and 0<=args.native_carmy_id<=2**31-1,
                   'public CUnit and separately observed native CArmy permit zero')
            self.binding={'pid':self.runtime['pid'],'process_create_time_100ns':self.runtime['process_create_time_100ns'],
                'generation':self.runtime['connection_generation'],'actor':self.runtime['player_character_id'],
                'episode':self.runtime['episode'],'army_id':args.army_id,'native_carmy_id':args.native_carmy_id}
            self.proof_pin=h.pin(self.e.root/self.runtime['source_proof']['path'])
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
            saved=self.case/'binding.actual.json'
            if saved.exists():
                prior=h.load(saved,1024*1024)
                h.need(prior['deadline_utc']==self.meta['deadline_utc'],'case deadline changed')
                h.need(all(prior['binding'][k]==v for k,v in self.binding.items() if k!='native_carmy_id'),
                       'case crossed owned runtime')
                self.binding=prior['binding']
            else:h.write_new(saved,{**self.meta,'binding':self.binding})
            self.check_process()
            h.write_new(self.attempt/'START.actual.json',{**self.meta,'binding':self.binding})

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
    p.add_argument('stage',choices=('baseline','Move-once','Move-post','advance','post'))
    for name in ('repo','relay-source','consumer-root','consumer-manifest','plan','runtime','features-binding',
                 'evidence-root','context','request-helper'):p.add_argument('--'+name,type=Path,required=True)
    for name in ('relay-sha256','request-helper-sha256','loaded-save-sha256','case-id','attempt','deadline-utc'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--army-id',type=int,required=True);p.add_argument('--native-carmy-id',type=int,required=True)
    p.add_argument('--state',type=Path)
    p.add_argument('--days',type=int,default=1)
    return p


def main():
    args=parser().parse_args()
    if not 1<=args.days<=30:raise ValueError('existing bounded stage range is1..30; absolute total remains90')
    h,c,a,ri=load_dependencies(args);live=None
    try:
        live=make_live_class(h,c,a,ri)(args)
        fn={'baseline':live.baseline,'Move-once':live.move_once,'Move-post':live.move_post,'advance':live.advance,'post':live.post}[args.stage]
        result=fn();path=h.write_new(live.attempt/'RESULT.actual.json',{**live.meta,'result':result})
        print(json.dumps({'phase':args.stage,'result':str(path),'phases_chained':False}));return 0
    except BaseException as error:
        if live is not None:h.write_new(live.attempt/'FAILURE.actual.json',{**live.meta,'error':str(error)[:4000],
            'pending_original_response':live.pending,'unknown_action_retry':False,'new_request_retry':False})
        raise

if __name__=='__main__':raise SystemExit(main())
