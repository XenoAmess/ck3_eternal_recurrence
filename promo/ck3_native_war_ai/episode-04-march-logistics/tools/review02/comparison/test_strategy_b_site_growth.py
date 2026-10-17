"""New semantic boundary checks only, using real endpoint/DATA/clock consumers."""
from pathlib import Path
import copy,hashlib,json,sys,tempfile,unittest
HERE=Path(__file__).resolve().parent
REPO=Path(__file__).resolve().parents[6]
sys.path[:0]=[str(REPO/'promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison'),str(REPO/'ck3_autonomous_player/src')]
import r10_compare as c,strategy_b as b
import strategy_b_site_growth as s

class Fixture:
 def __init__(self,root):self.root=Path(root);self.n=0
 def put(self,x):
  self.n+=1;p=self.root/(str(self.n)+'.json');z=json.dumps(x,separators=(',',':')).encode();p.write_bytes(z)
  return {'path':p.name,'bytes':len(z),'sha256':hashlib.sha256(z).hexdigest()}
 def sample(self,p,k,mutate=lambda x:None):
  proof=self.put({'synthetic':True});rt=dict(machine_id='synthetic',started_at_utc='2026-01-02T00:00:00Z',pid=k,process_create_time_100ns=k,
   connection_generation=1,episode=str(k),player_character_id=7,source_head='a'*40,native_dll_sha256='b'*64,source_proof=proof)
  plan=dict(build=dict(version='1.20.0.4',source_head='a'*40,native_dll_sha256='b'*64),t0_raw=1000,goal_province_id=99,arrival_states=['regular'],original_regiment_ids=[1])
  pp=self.put(plan);binding=dict(pid=k,process_create_time_100ns=k,generation=1,actor=7,episode=str(k));comm=self.put({'id':7});feat=self.put({})
  def endpoint(day):
   pos=dict(army_id=1,owner_character_id=7,controllable=True,in_combat=False,retreating=False,current_province_id=p,army_state='regular',route_province_ids=[],route_read_status='complete_empty',move_target_province_id=None)
   snap=dict(date_raw=1000+24*day,paused=True,map_ready=True,revision=10+day,native_revision=9+day,snapshot_id=str(day),played_character=dict(character_id=7,alive=True),played_character_gold=dict(raw=1,scale=100000),active_wars=[],player_armies=[pos],episode_run_id=str(k),diagnostics=dict(bridge_pid=k,connection_generation=1,hello=dict(expected_ck3_version='1.20.0.4',expected_ck3_sha256=c.EXE)))
   data=dict(record_index=0,persistent_regiment_id=101,chunk_index=0,current_soldiers=50,maximum_soldiers=50,chunk_army_regiment_id=1,status='available')
   family=dict(status='available',source='native_natural_supply_callback_entry_return',identity_basis='public_unit_and_native_carmy_full_ids_at_invocation',observer_installed=True,oldest_available_sequence=day,latest_sequence=day,overwritten_events=0,unattributed_capture_failures=0,event_count=day,events=[])
   if day:
    values=lambda stock:dict(province_id=p,supply_raw=stock,last_supply_update_date_raw64=600,supply_updated_byte_raw=1)
    family['events']=[dict(sequence=1,army_id=1,native_carmy_id=1,passed_date_raw64=600,caller_return_rva=1,before=values(1000000),after=values(1100000),same_instance_after=True,capture_failure_flags=0)]
   row=dict(army_id=1,native_carmy_id=1,status='available',native_army_resolution_v1=dict(status='available',ready=True,entry_full_id=1),regiment_count=1,current_soldiers=50,maximum_soldiers=50,regiment_strengths=[dict(army_regiment_id=1,current_soldiers=50,maximum_soldiers=50,scale=1)],regiment_replenishment_records_v1=[dict(army_regiment_id=1,status='available',ready=True,source='native_all_data_records',native_data_record_count=1,records=[data])],current_supply_raw=1000000+100000*day,current_supply_scale=100000,current_supply_capacity_raw=30000000,current_supply_capacity_scale=100000,current_supply_change_monthly_raw=0,actual_supply_callback_observations_v1=family,source_derived_next_daily_supply_frame_inputs_v1=dict(current_date_storage_raw64=600))
   if day:mutate(row)
   q=dict(accepted=True,status='available',army_strengths=[row],army_strengths_query_scope=dict(army_ids=[1],published_scope_status='available'),queried_snapshot_id=str(day),queried_revision=10+day,queried_native_revision=9+day,queried_date_raw=snap['date_raw'],queried_connection_generation=1,queried_episode_run_id=str(k))
   return dict(day=day,snapshot=self.put(dict(body=snap)),army_result=self.put(q),strategy_army_ids=[1],commander=dict(source=comm,pointer='/id'),loaded_features=dict(source=feat,pointer=''))
  before,after=endpoint(0),endpoint(1)
  clock=dict(state='triggered',generation=1,starting_date_raw=1000,target_date_raw=1024,last_observed_date_raw=1024,trigger_date_raw=1024,speed=5,mode='terminal_or_sentinel',army_count=0,combat_count=0,completed_daily_ticks=1,intermediate_pause_count=0,overshoot_days=0,signed_date_delta_from_target_raw=0,abnormal=False,pause_observed=True,pause_wrapper_called=True,trigger_reasons=['date_deadline'])
  header=dict(machine_id='synthetic',source_head='a'*40,binding=binding,plan=pp,helper=proof)
  claim=self.put(dict(**header,before=before,previous_complete=None,start=1000,target=1024))
  complete=self.put(dict(**header,claim=claim,before=before,after=after,day=dict(day=1,clock_source=self.put(dict(clock=clock)),paused_snapshot=after['snapshot'],strategy_army_ids=[1]),previous_complete=None,qualified=True))
  return self.put(dict(schema='xar.e04.B-rest-site-input.v1',province_id=p,army_id=1,runtime=self.put(rt),normal_day=complete))

from xar_autoplayer.bridge import army_actual_supply_callback_observations_contract as C
from xar_autoplayer.bridge import army_actual_supply_callback_observation_summary as S

class RAMFixture(Fixture):
 def __init__(self):super().__init__(HERE/'synthetic-not-written');selblobs={}
 def put(self,x):
  self.n+=1;p=str(self.n)+'.json';z=json.dumps(x,separators=(',',':')).encode();selblobs[p]=z
  return dict(path=p,bytes=len(z),sha256=hashlib.sha256(z).hexdigest())
class RAMReader(c.Evidence):
 def __init__(self,x):super().__init__(x.root);selblobs=x.blobs
 def raw(self,p):
  z=selblobs[p['path']];assert len(z)==p['bytes']and c.digest(z)==p['sha256'];return z
class EventProvinceChain(unittest.TestCase):
 def test_known_stationary_two_sites_accept_and_cross_province_or_missing_refuse(self):
  x=RAMFixture();refs=[x.sample(20,11),x.sample(21,12)];e=RAMReader(x)
  baseline=e.json(e.json(refs[0])['normal_day'])['before']
  plan=dict(baseline=baseline,strategies={'B':dict(rest_province_ids=[20,21],site_actual_stock_increase_evidence=refs)})
  result=s.qualify_plan_sites(plan,e,b)
  self.assertEqual([v['province_id']for v in result['sites']],[20,21]);self.assertFalse(result['B_live_readiness_granted'])
  for side in ('before','after'):
   for value in (21,None,'absent'):
    with self.subTest(side=side,value=value):
     def mutate(row):
      v=row['actual_supply_callback_observations_v1']['events'][0][side]
      if value=='absent':v.pop('province_id')
      else:v['province_id']=value
     x=RAMFixture();ref=x.sample(20,11,mutate)
     with self.assertRaisesRegex(ValueError,'Province'):s.qualify_site(RAMReader(x),ref,b)

class OptionalProvince(unittest.TestCase):
 def test_legacy_null_known_and_invalid_province(self):
  values=dict(supply_raw=10,last_supply_update_date_raw64=100,supply_updated_byte_raw=1)
  event=dict(sequence=1,army_id=7,native_carmy_id=8,passed_date_raw64=100,caller_return_rva=1,before=values,after=values,same_instance_after=True,capture_failure_flags=0)
  base=dict(status='available',source='native_natural_supply_callback_entry_return',identity_basis='public_unit_and_native_carmy_full_ids_at_invocation',observer_installed=True,oldest_available_sequence=1,latest_sequence=1,overwritten_events=0,unattributed_capture_failures=0,event_count=1,events=[event])
  def check(value):
   n=C.normalize_actual_supply_callback_observations_v1(value,current_army_id=7,current_native_carmy_id=8)
   return n['events'][0],S.summarize_actual_supply_callback_observations_v1({'actual_supply_callback_observations_v1':n})['events'][0]
  n,s=check(base);self.assertNotIn('province_id',n['before']);self.assertNotIn('province_before_id',s);self.assertNotIn('province_after_id',s)
  for value in (None,2624,-2**31,2**31-1):
   b=copy.deepcopy(base)
   for side in ('before','after'):b['events'][0][side]['province_id']=value
   n,s=check(b);self.assertIs(n['before']['province_id'],None) if value is None else self.assertEqual(n['before']['province_id'],value)
   self.assertEqual(s['province_before_id'],value);self.assertEqual(s['province_after_id'],value)
  for value in (True,False,-2**31-1,2**31):
   b=copy.deepcopy(base);b['events'][0]['after']['province_id']=value
   with self.assertRaises(ValueError):check(b)


if __name__=='__main__':unittest.main(verbosity=2)
