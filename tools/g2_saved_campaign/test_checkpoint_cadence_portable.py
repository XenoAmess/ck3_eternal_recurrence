"""Portable offline acceptance: actual coroutine excerpts and compact immutable trace."""
from pathlib import Path
import ast,asyncio,collections,copy,hashlib,importlib.util,json

def main():
    O=Path(__file__).resolve().parent
    F=O/'fixtures'
    def load(name,path):
        spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    old=load('old_checkpoint',F/'checkpoint_cadence_loop.py')
    new=load('new_checkpoint',O/'root_checkpoint_cadence.py')
    trace_fixture=json.loads((F/'checkpoint_cadence_trace.json').read_text(encoding='utf-8'))
    events=trace_fixture['events'];bodies={int(k):v for k,v in trace_fixture['bodies'].items()}
    checks=[]
    def pending(event):
        p={k:copy.deepcopy(v) for k,v in event.items() if k not in ('after','after_metrics_response','date_delta_raw','cumulative_observation_counts')}
        p['checkpoint_context']=new.checkpoint_context_from_auto(bodies[event['auto_sequence']])
        return p
    contexts=[(e['global_turn'],new.checkpoint_context_from_auto(bodies[e['auto_sequence']])) for e in events if e['selected_step']=='life-advance']

    fixture=bodies[1475]
    for change in ('combat','enemy_route','war_change','unknown_phase'):
        changed=copy.deepcopy(fixture)
        war=changed['result']['war_progress_after']['wars'][0]
        if change=='combat':war['player_armies'][0]['in_combat']=True
        elif change=='enemy_route':war['enemy_armies'][0]['route_province_ids']=[123]
        elif change=='war_change':war['war_id']=72
        else:changed['plan']['phase']='unknown_new_phase'
        assert new.checkpoint_context_from_auto(changed) is None,change
    assert all(c is not None for _,c in contexts[:6]) and contexts[-1][1] is None
    checks.append({'name':'actual six pure siege advances qualify; completion, new combat/route/war/unknown phase retain5','status':'GREEN'})
    def loop_method(path,helper,class_name):
        tree=ast.parse(path.read_text(encoding='utf-8'))
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==class_name)
        fn=next(n for n in cls.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='full_loop')
        writes=[]
        env={'AUTO':'AUTO','METRICS':'METRICS','SEMANTIC':'SEMANTIC','SAVE':'SAVE',
             'Q':Path('OFFLINE-Q'),'OUTBOX':Path('OFFLINE-OUT'),'frame':lambda b,**k:dict(b),
             'atomic':lambda path,row,**k:writes.append((str(path),copy.deepcopy(row))),
             'checkpoint_after_settled_cycle':helper.checkpoint_after_settled_cycle,
             'checkpoint_context_from_auto':new.checkpoint_context_from_auto}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),str(path),'exec'),env)
        return env['full_loop'],writes
    class OfflineQueue:
        def __init__(self,method,source):
            self.full_loop=method.__get__(self);self.source=source;self.index=0;self.current=None
            self.initial_save={'offline':True};self.checkpoint_bootstrap_verified=True
            self.loop_count=0;self.next_sequence=1;self.expected_lifecycle_binding={}
            self.saves=[];self.calls=[];self.guard_count=0
            self.full_loop_state={'completed_cycles':source[0]['global_turn']-1,'start_date_raw':source[0]['before']['date_raw'],
              'before':copy.deepcopy(source[0]['before']),'before_metrics_response':'OFFLINE-INITIAL',
              'pending_cycle':None,'pending_checkpoint':None,'terminal':None,'counts':collections.defaultdict(int),
              'checkpoint_dirty_since_save':False}
        def guard(self):self.guard_count+=1
        def require_camera_pixel_admission(self):pass
        def consume_sequence(self,request):
            seq=self.next_sequence;self.next_sequence+=1;return seq
        def persist_loop_state(self):pass
        async def generated(self,session,tool,arguments=None):
            self.calls.append((tool,arguments));seq=self.next_sequence;self.next_sequence+=1
            if tool=='AUTO':
                self.current=self.source[self.index];self.index+=1
                self.last_auto_observation=copy.deepcopy(self.current['observation'])
                result=copy.deepcopy(bodies[self.current['auto_sequence']])
            elif tool=='METRICS':result=copy.deepcopy(self.current['after'])
            elif tool=='SEMANTIC':result=copy.deepcopy(self.full_loop_state['before'])
            elif tool=='SAVE':
                assert arguments=={'expected_revision':self.full_loop_state['before']['revision']}
                self.saves.append(self.full_loop_state['completed_cycles'])
                result={'checkpoint':{'status':'saved','date_raw':self.full_loop_state['before']['date_raw']}}
            else:raise AssertionError('unknown offline tool')
            return result,Path('OFFLINE-RESPONSES')/('%04d.json'%seq)
        def finish_cumulative_checkpoint(self,saved,path):
            self.full_loop_state['counts']['checkpoint_saved']+=1
            self.full_loop_state['checkpoint_dirty_since_save']=False
            self.full_loop_state['pending_checkpoint']=None
    async def actual_trace():
        old_method,old_writes=loop_method(F/'checkpoint_cadence_loop.py',old,'OriginalQueueFixture')
        new_method,new_writes=loop_method(F/'checkpoint_cadence_loop.py',new,'CandidateQueueFixture')
        oq,nq=OfflineQueue(old_method,events),OfflineQueue(new_method,events)
        await oq.full_loop(None,{'arguments':{'max_turns':len(events)}},Path('offline-control-old'))
        await nq.full_loop(None,{'arguments':{'max_turns':len(events)}},Path('offline-control-new'))
        assert oq.saves==[1675,1680,1685,1690],oq.saves
        assert nq.saves==[1682,1690],nq.saves
        assert oq.index==nq.index==17
        assert oq.full_loop_state['before']==nq.full_loop_state['before']==events[-1]['after']
        deferred=[row for _,row in new_writes if row.get('status')=='stable_player_siege_checkpoint_deferred_to_cycle_10']
        assert [row['global_turn'] for row in deferred]==[1675,1685]
        assert all(row['new_gameplay_mutations_observed'] is True for row in deferred)
        return {'old_saves':oq.saves,'candidate_saves':nq.saves,'AUTO_count':nq.index,
                'date_delta_raw':nq.full_loop_state['before']['date_raw']-events[0]['before']['date_raw'],
                'actual_generated_method':'FreshQueue.full_loop AST loaded, exact existing coroutine',
                'transport':'offline fake generated/atomic/frame/persistence only; no Game/MCP/OBS'}
    trace=asyncio.run(actual_trace())
    checks.append({'name':'actual FreshQueue.full_loop async replay of 17 immutable settled cycles; four saves become two, identical AUTO/date endpoint','status':'GREEN',**trace})
    event=events[1];p=pending(event)
    for mismatch in ('revision','native_revision','date_raw','actor_character_id','episode_run_id'):
        after=copy.deepcopy(event['after']);after[mismatch]=after[mismatch]+1 if isinstance(after[mismatch],int) else 'other'
        assert not new._paired_context(p,after)
    state={'completed_cycles':1675,'terminal':None,'checkpoint_dirty_since_save':False}
    bad=copy.deepcopy(p);bad['checkpoint_context']=None
    assert new.checkpoint_after_settled_cycle(state,bad,event['after']) is True
    assert state['checkpoint_last_decision']['interval_settled_cycles']==5
    for turn in (1,2,3,4,5,10,100):
        state={'completed_cycles':turn,'terminal':None,'checkpoint_dirty_since_save':False}
        q=pending(events[0]);assert not new.checkpoint_after_settled_cycle(state,q,events[0]['after'])
    checks.append({'name':'paired frame mismatches cannot grant interval10; absent proof retains5; clean readonly chains never resave','status':'GREEN'})
    victory=trace_fixture['victory_event']
    state={'completed_cycles':1691,'terminal':None,'checkpoint_dirty_since_save':False}
    assert not new.checkpoint_after_settled_cycle(state,victory,victory['after'])
    assert state['checkpoint_last_decision']['interval_settled_cycles']==5
    for key in ('submitted_pending','construction_start_verified','lifestyle_material_verified'):
        q=pending(events[0]);q['observation'][key]=True
        state={'completed_cycles':5,'terminal':None,'checkpoint_dirty_since_save':False}
        assert new.checkpoint_after_settled_cycle(state,q,q['before'])
        state['completed_cycles']=10
        again=pending(events[0]);assert not new.checkpoint_after_settled_cycle(state,again,again['before'])
        assert state['checkpoint_due_after_readonly_chain'] is True
        state['completed_cycles']=11
        assert new.checkpoint_after_settled_cycle(state,q,q['before'])
        state['checkpoint_dirty_since_save']=False
        state['completed_cycles']=12
        assert not new.checkpoint_after_settled_cycle(state,again,again['before'])
        assert state['checkpoint_due_after_readonly_chain'] is False
    state={'completed_cycles':10,'terminal':'actor_handoff','checkpoint_dirty_since_save':True}
    assert not new.checkpoint_after_settled_cycle(state,p,event['after'])
    provenance=json.loads((F/'checkpoint_cadence_provenance.json').read_text(encoding='utf-8'))
    tree=ast.parse((F/'checkpoint_cadence_loop.py').read_text(encoding='utf-8'))
    for name,key in [('OriginalQueueFixture','original_full_loop_ast_sha256'),('CandidateQueueFixture','candidate_full_loop_ast_sha256')]:
        cls=next(c for c in tree.body if isinstance(c,ast.ClassDef) and c.name==name)
        fn=next(n for n in cls.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='full_loop')
        assert hashlib.sha256(ast.dump(fn).encode()).hexdigest()==provenance[key]
    checks.append({'name':'nonroutine/material/pending keep five-cycle due; readonly carry, dirty and terminal preserved; fixture coroutine AST matches actual source excerpt','status':'GREEN'})
    prewar=json.loads((F/'checkpoint_carry_prewar_trace.json').read_text(encoding='utf-8'))
    state={'completed_cycles':prewar['boundary']['global_turn'],'terminal':None,'checkpoint_dirty_since_save':True}
    for key in ('boundary','next_readonly'):
        event=prewar[key];state['completed_cycles']=event['global_turn']
        assert not new.checkpoint_after_settled_cycle(state,event,event['after'])
        assert state['checkpoint_due_after_readonly_chain'] is True
    event=prewar['advance'];state['completed_cycles']=event['global_turn']
    assert new.checkpoint_after_settled_cycle(state,event,event['after'])
    checks.append({'name':'actual prewar readonly %5 due carries from turn2950 through2951 to next seven-day advance2961','status':'GREEN'})
    report={'status':'GREEN','offline_only':True,'checks':checks,'source_sha256':hashlib.sha256((O/'root_checkpoint_cadence.py').read_bytes()).hexdigest(),
            'limits':['Fake transport/persistence/frame only; no Game/MCP/OBS/window/process calls.',
                      'Routine SAVE becomes due every10 settled cycles; readonly-chain and player-decision deferral can postpone actual SAVE.',
                      'No gameplay evidence cache, strategy change, or native guard change.']}
    print(json.dumps(report))

if __name__ == '__main__':
    main()
