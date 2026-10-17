"""New C gaps only: normal provider, prepared-session coherence, marine state.
All process/transport data below are explicitly SYNTHETIC. No SDK import.
"""
from copy import deepcopy
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from types import ModuleType,SimpleNamespace
from unittest.mock import patch

HERE=ROOT=Path(__file__).resolve().parent
REPO=HERE.parents[5]
REL=Path('promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02')
def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def pin(path):
 import hashlib
 b=Path(path).read_bytes();return {'path':str(Path(path).resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
entry=module(HERE/'phased_relay.py','C611_external_entry')
op=module(HERE/'operation_root_relay.py','C611_normal_operation')
a=module(HERE/'strategy_c_next_decision.py','C611_adapter');c=a.c;reader=a._reader()
factory=module(REPO/REL/'strategy_c/test_operation_root_relay.py','C611_existing_fixture_factory_only')
guard_module=module(REPO/REL/'runtime_binding.py','C611_unchanged_runtime_guard')

class ConnectedGaps(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='SYNTHETIC-C611-',dir=ROOT);self.addCleanup(self.temp.cleanup)
  self.f=factory.Fixture(Path(self.temp.name));self.f.args.repo=REPO;self.f.args.army_id=1
  self.f.plan.update(max_natural_days=90,raw_per_day=24,goal_province_id=30,
   original_regiment_ids=[501],arrival_states=['regular','sieging'],
   follow_after_arrival_to_day90=True,post_arrival_policy='hold-arrival-position-until-day90')
  self.f.plan['strategies']['C']={'mode':'whole-via','waypoint_province_ids':[20],'route_preview':None}
  self.f.flush();self.io=None;self.moves=[];self.query_count=0;self.wrong_parent=False
 def construct(self):
  with patch.object(op.subprocess,'run',return_value=SimpleNamespace(stdout=self.f.source+'\n')):
   return op.Live(self.f.args,transport=self.f.transport,process_probe=lambda pid:134000000000000123,
    machine_probe=lambda repo:self.f.machine,clock=lambda:self.f.now)
 def bundle(self):
  f=self.f
  return {'machine_id':f.machine,'source_head':f.source,'deadline_utc':f.args.deadline_utc,'repo':str(REPO),
   'runtime_request_budget_bytes':f.args.max_runtime_total_bytes,'army_id':1,'case_id':f.args.case_id,
   'evidence_roots':[str(f.scene)],'runtime':f.runtime,'current_loaded_features':{'source':pin(f.args.context),'pointer':'/identity'},
   **{key:pin(getattr(f.args,key)) for key in ('context','runtime_proof','plan','prepared','request_helper','live_binding')},
   'capacity':pin(f.scene/'capacity.json'),'modules':{'root_relay':pin(HERE/'operation_root_relay.py'),
    'next_adapter':pin(HERE/'strategy_c_next_decision.py'),'strategy_guard':pin(HERE/'strategy_c.py'),
    'comparison_reader':pin(HERE.parent/'comparison/r10_compare.py'),'common_horizon':pin(HERE/'common_horizon.py')}}
 def snapshot(self,day,revision,position,state,route):
  return {'snapshot_id':f'SYNTHETIC-{day}-{revision}','revision':revision,'native_revision':revision-1,
   'date_raw':123456+24*day,'paused':True,'map_ready':True,'episode_run_id':'synthetic-new-cold-42',
   'played_character':{'character_id':42,'alive':True},'played_character_gold':{'raw':1000000-day,'scale':100000},
   'diagnostics':{'bridge_pid':901,'connection_generation':1,'hello':{'expected_ck3_version':'1.20.0.4','expected_ck3_sha256':reader.EXE}},
   'active_wars':[],'synthetic_commander_id':42,'synthetic_features':{'SYNTHETIC':True},
   'player_armies':[{'army_id':1,'owner_character_id':42,'controllable':True,'current_province_id':position,
    'army_state':state,'army_state_code':{'regular':1,'sieging':3,'embarked':4,'moving':7}[state],
    'route_province_ids':route,'route_source_count':len(route),'route_read_status':'complete_nonempty' if route else 'complete_empty',
    'move_target_province_id':route[-1] if route else None,'move_target_observable':bool(route),'in_combat':False,'retreating':False}]}
 def transport(self,identifier,tool,arguments,timeout):
  req={'request_id':identifier,'tool':tool,'arguments':arguments}
  row={'machine_id':self.f.machine,'is_error':False,'request':req,'body':deepcopy(self.current)}
  if tool=='ck3_query_army_strengths':
   self.query_count+=1;s=self.current
   q={'accepted':True,'step':'query-army-strengths-v1','army_strengths_profile':'ordinary_core_v1','query_sequence':self.query_count,
    'army_strengths_query_scope':{'army_ids':[1],'published_scope_status':'available'},
    **{qk:s[sk] for qk,sk in [('queried_snapshot_id','snapshot_id'),('queried_revision','revision'),
     ('queried_native_revision','native_revision'),('queried_date_raw','date_raw'),('queried_episode_run_id','episode_run_id')]},
    'queried_connection_generation':1,'army_strengths':[{'army_id':1,'native_carmy_id':99,'status':'available',
     'regiment_count':1,'current_soldiers':100,'maximum_soldiers':100,
     'regiment_strengths':[{'army_regiment_id':501,'current_soldiers':100,'maximum_soldiers':100,'scale':1}],
     'regiment_replenishment_records_v1':[{'army_regiment_id':501,'status':'available','source':'native_all_data_records',
      'ready':True,'unavailable_reason':None,'native_data_record_count':0,'records':[]}],
     'current_supply_raw':1000000,'current_supply_capacity_raw':10000000,
     'current_supply_scale':100000,'current_supply_capacity_scale':100000,
     'current_movement_progress':{'source':'native_current_route_edge'}}]}
   raw=(self.f.scene/'state-a01/native-session' if self.wrong_parent else self.io.native_session)/'army-query-history-results'/f'q{self.query_count}.json'
   raw.parent.mkdir(parents=True,exist_ok=True);raw.write_text(json.dumps(q),encoding='utf-8')
   row['body']={'accepted':True};row['army_history_evidence']={'machine_id':self.f.machine,'request_id':identifier,
    'query_sequence':self.query_count,'raw_result_reference':{**pin(raw),'kind':'complete-driver-army-query-result-json-v1','wire_bytes_preserved':False}}
  elif tool!='ck3_take_snapshot':self.moves.append(tool);raise AssertionError('unexpected action')
  (self.f.run/'requests'/(identifier+'.json')).write_text(json.dumps(req))
  (self.f.run/'responses'/(identifier+'.json')).write_text(json.dumps(row));return row
 def inputs(self,observation,refs,day):
  record={'day':day,'snapshot':refs['snapshot'],'army_result':refs['strength'],'strategy_army_ids':[1],
   'commander':{'source':refs['snapshot'],'pointer':'/body/synthetic_commander_id'},
   'loaded_features':{'source':refs['snapshot'],'pointer':'/body/synthetic_features'}}
  ev=entry.Evidence([self.f.scene],reader,runtime={'source_head':self.f.source,'machine_id':self.f.machine})
  runtime={'machine_id':self.f.machine,'pid':901,'process_create_time_100ns':134000000000000123,
   'connection_generation':1,'episode':'synthetic-new-cold-42','player_character_id':42}
  out=a.read_inputs(self.f.plan,runtime,record,ev);a._whole_data(self.f.plan,out);return out
 def clock(self,day):
  end=123456+24*day
  return {'state':'triggered','starting_date_raw':end-24,'target_date_raw':end,'last_observed_date_raw':end,
   'trigger_date_raw':end,'generation':day,'speed':5,'completed_daily_ticks':1,'overshoot_days':0,
   'signed_date_delta_from_target_raw':0,'army_count':0,'combat_count':0,'intermediate_pause_count':0,
   'abnormal':False,'pause_observed':True,'mode':'terminal_or_sentinel','trigger_reasons':['date_deadline'],'pause_wrapper_called':True}
 def test_external_provider_normally_constructs_own_readers_and_requires_horizon_pin(self):
  bundle=self.bundle();guard=guard_module.OperationGuard(self.f.args.live_binding,self.f.args.live_binding_sha256,
   context=self.f.context,runtime=guard_module.proof_runtime(self.f.proof),scene_root=self.f.scene,
   source_head=self.f.source,machine_id=self.f.machine,run_id=self.f.run_id,
   max_runtime_total_bytes=self.f.args.max_runtime_total_bytes,deadline_utc=self.f.args.deadline_utc,
   normal_save_sha256='b'*64,clock=lambda:self.f.now)
  with patch.object(entry,'operation_guard',return_value=(guard_module,guard)):
   missing=deepcopy(bundle);missing['modules'].pop('common_horizon')
   with self.assertRaisesRegex(ValueError,'common_horizon'):entry.prepare(missing)
   self.assertEqual(entry.prepare(bundle)['status'],'SOURCE-COMPOSITION-PREPARED')
  constructed=[];real_module=entry.module
  def normal(args):
   constructed.append(args)
   return op.Live(args,transport=self.f.transport,process_probe=lambda pid:134000000000000123,
    machine_probe=lambda repo:self.f.machine,clock=lambda:self.f.now)
  def imported(path,name):
   if Path(path)==HERE/'operation_root_relay.py':return SimpleNamespace(OPERATION_BINDING_API=op.OPERATION_BINDING_API,Live=normal)
   return real_module(path,name)
  top=ModuleType('xar_autoplayer');top.__path__=[];bridge=ModuleType('xar_autoplayer.bridge');bridge.__path__=[]
  native=ModuleType('xar_autoplayer.bridge.native_driver');bridge.native_driver=native
  with (patch.object(entry,'operation_guard',return_value=(guard_module,guard)),patch.object(entry,'module',side_effect=imported),
   patch.object(op.subprocess,'run',return_value=SimpleNamespace(stdout=self.f.source+'\n')),
   patch.dict(sys.modules,{'xar_autoplayer':top,'xar_autoplayer.bridge':bridge,'xar_autoplayer.bridge.native_driver':native})):
   io,nd=entry.provider(bundle,SimpleNamespace(attempt='new-provider',stage='admit'))
  self.assertEqual(len(constructed),1);self.assertIs(io.strength_at.__func__,op.Live.strength_at)
  self.assertIs(io.coherent_stop_core.__func__,op.Live.coherent_stop_core)
  self.assertEqual(constructed[0].runtime_guard,REPO/REL/'runtime_binding.py')
  self.assertEqual(io.native_session,self.f.scene/'state-a02/native-session');self.assertFalse(self.f.calls)
  self.assertEqual(io.live_operation_guard.pin,pin(self.f.args.live_binding));self.assertIs(nd,native)
 def test_coherent_state_a02_marine_suffix_and_landing_use_complete_real_reader(self):
  self.io=self.construct();self.f.transport.request=self.transport
  self.current=self.snapshot(0,10,10,'regular',[]);raw,refs=self.io.frame('S0');initial=self.inputs(raw,refs,0)
  state=c.start(self.f.plan,initial);b=initial['binding']
  preview={'accepted':True,**{q:b[k] for q,k in [('queried_snapshot_id','snapshot_id'),('queried_revision','revision'),
   ('queried_native_revision','native_revision'),('queried_connection_generation','connection_generation'),('queried_episode_run_id','episode')]},
   'route_preview':{'status':'available','army_id':1,'origin_province_id':10,'target_province_id':20,
    'previewed_date_raw':123456,'route_province_ids':[11,20]}}
  state,call=c.propose_move(self.f.plan,state,initial,preview);self.assertEqual(call['tool'],'ck3_move_army')
  self.current=self.snapshot(0,11,10,'embarked',[11,20]);raw,refs=self.io.frame('applied')
  state=c.observe(self.f.plan,state,self.inputs(raw,refs,0));self.assertEqual(state['phase'],'marching')
  stopped=self.snapshot(1,12,11,'embarked',[20]);self.current=self.snapshot(1,13,11,'embarked',[20])
  raw,refs=self.io.coherent_stop_core(stopped,'post-status');sea=self.inputs(raw,refs,1);sea['clock']=self.clock(1)
  state=c.observe(self.f.plan,state,sea);self.assertEqual(a.next_decision(self.f.plan,state,sea)['status'],'continue_exact_day')
  self.assertIn('state-a02',refs['strength']['path']);self.assertEqual(raw['strength']['army_strengths'][0]['regiment_replenishment_records_v1'][0]['records'],[])
  self.current=self.snapshot(2,14,20,'regular',[]);raw,refs=self.io.frame('landed');land=self.inputs(raw,refs,2);land['clock']=self.clock(2)
  state=c.observe(self.f.plan,state,land);self.assertEqual((state['phase'],state['arrivals'][0]['observed_interval_days']),('ready',[1,2]))
  self.assertFalse(self.moves)
 def test_coherent_reader_rejects_stale_session_state_drift_and_original_unpaused(self):
  self.io=self.construct();self.f.transport.request=self.transport
  stopped=self.snapshot(1,12,11,'embarked',[20]);self.current=self.snapshot(1,13,11,'embarked',[20]);self.wrong_parent=True
  with self.assertRaisesRegex(RuntimeError,'parent/kind'):self.io.coherent_stop_core(stopped,'wrong-parent')
  self.wrong_parent=False;self.current=self.snapshot(1,14,11,'moving',[20]);before=self.query_count
  with self.assertRaisesRegex(RuntimeError,'Army/date/state'):self.io.coherent_stop_core(stopped,'changed-state')
  self.assertEqual(self.query_count,before)
  stopped['paused']=False
  with self.assertRaisesRegex(RuntimeError,'must be paused'):self.io.coherent_stop_core(stopped,'not-paused')
  self.assertFalse(self.moves)
 def test_CStages_shared_budget_keeps_actual_prepared_native_session_and_whole_run(self):
  self.io=self.construct();stage=entry.CStages(self.io,SimpleNamespace(),self.bundle())
  self.assertIsNotNone(stage.horizon)
  before=self.io.used_bytes()
  driver=self.io.native_session/'driver-state.json';driver.write_bytes(b'SYNTHETIC-Driver-complete-state\n')
  calls=self.io.run/'mcp-calls.jsonl';calls.write_bytes(b'SYNTHETIC-root-MCP-envelope\n')
  self.assertEqual(self.io.used_bytes()-before,driver.stat().st_size+calls.stat().st_size)
  stale=self.f.scene/'state-a01/native-session';stale.mkdir(parents=True)
  (stale/'stale.json').write_bytes(b'SYNTHETIC-inactive-session-is-not-current\n')
  self.assertEqual(self.io.used_bytes()-before,driver.stat().st_size+calls.stat().st_size)
  stage.runtime_budget.limit_bytes=self.io.used_bytes()+reader.MAX_FILE+65536-1
  with self.assertRaisesRegex(ValueError,'cannot reserve'):
   self.io.request('no-capacity','ck3_take_snapshot',{})
  self.assertFalse(self.f.calls)

if __name__=='__main__':unittest.main(verbosity=2)
