"""New synthetic connected clock cases; no SDK, game or old test execution."""
from copy import deepcopy
import argparse, hashlib, importlib.util, json
from pathlib import Path
import sys, tempfile, types, unittest
HERE=Path(__file__).resolve().parent
REPO=Path.cwd()
REL='promo/ck3_native_war_ai/episode-04-march-logistics/tools/review02/comparison'
sys.dont_write_bytecode=True
parser=argparse.ArgumentParser();parser.add_argument('--repo',type=Path,default=REPO)
parser.add_argument('--candidate-root',type=Path);parser.add_argument('--scratch-root',type=Path)
options,rest=parser.parse_known_args()
REPO=options.repo;sys.path[:0]=[str(REPO/REL),str(REPO/'ck3_autonomous_player/src')]
import r10_compare as c
import test_r10_compare as fixture_module
import strategy_b as b
def read_module(path,name):
	spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
if options.candidate_root:
	build=read_module(options.candidate_root/'build_candidate.py','B_candidate_builder')
	all_sources=build.sources();source=all_sources[REL+'/strategy_b.py'][1]
	b=types.ModuleType('strategy_b');b.__file__=str(REPO/REL/'strategy_b.py');exec(compile(source,b.__file__,'exec'),b.__dict__);sys.modules['strategy_b']=b
	adapter=read_module(REPO/REL/'strategy_b_next.py','B_real_next_candidate')
	h=read_module(options.candidate_root/'strategy_b_common_horizon.py','B_common_candidate')
	stage=types.ModuleType('B_stages_candidate');stage.__file__=str(REPO/REL/'strategy_b_stages.py')
	exec(compile(all_sources[REL+'/strategy_b_stages.py'][1],stage.__file__,'exec'),stage.__dict__)
else:
	import strategy_b_next as adapter
	import strategy_b_common_horizon as h
	import strategy_b_stages as stage
class MemoryPath:
	"""Only the existing Fixture's tiny JSON writes use this in-memory store."""
	files={}
	def __init__(self,p):self.value=str(p)
	def __truediv__(self,p):return MemoryPath(self.value+'/'+str(p))
	@property
	def name(self):return self.value.rsplit('/',1)[-1]
	def write_bytes(self,raw):self.files[self.name]=raw
	def read_bytes(self):return self.files[self.name]
class Harness:
	def __init__(self,root):
		self.root=Path(root);self.requests=[];MemoryPath.files={}
		old=fixture_module.Path;fixture_module.Path=MemoryPath
		try:self.f=fixture_module.Fixture('memory')
		finally:fixture_module.Path=old
		self.plan=self.f.plan;self.plan.update(follow_after_arrival_to_day90=True,post_arrival_policy=h.POLICY)
		self.arm=deepcopy(self.f.results['arms'][1]);self.rt=self.arm['runtime']
		def wire(ep):
			ep=deepcopy(ep)
			def qedit(q):
				for row in q['army_strengths']:
					aid=row['army_id'];row['native_carmy_id']=1000+aid
					row['native_army_resolution_v1']={'status':'available','ready':True,'branch':'resolved','raw_reference':1000+aid,'entry_full_id':1000+aid,'reference_index':aid,'storage_capacity':128}
					for g in row['regiment_replenishment_records_v1']:
						g.update(ready=True,source='native_all_data_records')
						for r in g['records']:r.update(status='available',persistent_regiment_id=-(2**31)+g['army_regiment_id']-1,chunk_army_regiment_id=g['army_regiment_id'])
			ep['army_result']=self.f.edit(ep['army_result'],qedit)
			def sedit(v):
				s=v['body'];s['speed']=5;s['diagnostics']['connected']=True
				s['diagnostics']['hello'].update(pid=s['diagnostics']['bridge_pid'],connection_generation=1,game_adapter_status='ready',ck3_build_match=True)
				for p in s['player_armies']:p.update(source='native',controllable=True,in_combat=False,retreating=False)
			ep['snapshot']=self.f.edit(ep['snapshot'],sedit);return ep
		self.plan['baseline']=wire(self.plan['baseline'])
		self.arm['cold_start']=wire(self.arm['cold_start']);self.arm['observations']=[wire(e) for e in self.arm['observations']]
		for day,ep in zip(self.arm['days'],self.arm['observations']):day['paused_snapshot']=ep['snapshot']
		self.arrival=self.arm['observations'][-1]
		self.after=deepcopy(self.arrival);self.after['day']=3
		def aftersnap(v):
			s=v['body'];s.update(date_raw=1072,revision=13,native_revision=12,snapshot_id='B:3');s['played_character_gold']['raw']-=42
		self.after['snapshot']=self.f.edit(self.after['snapshot'],aftersnap)
		def afterquery(q):
			q.update(queried_date_raw=1072,queried_revision=13,queried_native_revision=12,queried_snapshot_id='B:3')
			row=q['army_strengths'][0];row['current_supply_raw']-=700
			row['regiment_strengths'][0]['current_soldiers']-=1;row['current_soldiers']-=1
			row['regiment_replenishment_records_v1'][0]['records'][0]['current_soldiers']-=1
		self.after['army_result']=self.f.edit(self.after['army_result'],afterquery)
		self.files=MemoryPath.files;self.c=c
		class E(c.Evidence):
			def raw(e,p):
				raw=self.files[Path(p['path']).name]
				if len(raw)!=p['bytes'] or hashlib.sha256(raw).hexdigest()!=p['sha256']:raise ValueError('synthetic exact pin differs')
				return raw
		self.e=E(self.root)
		self.binding={'pid':self.rt['pid'],'process_create_time_100ns':self.rt['process_create_time_100ns'],
			'generation':1,'actor':7,'episode':self.rt['episode']}
		def pin(p):
			p=Path(p);raw=p.read_bytes() if p.is_file() else self.files[p.name]
			return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
		def load(p):
			p=Path(p);return c.parse(p.read_bytes() if p.is_file() else self.files[p.name])
		def verify(p):
			actual=pin(p['path']);assert actual['bytes']==p['bytes'] and actual['sha256']==p['sha256']
		def write(p,obj):
			with Path(p).open('xb') as f:f.write((json.dumps(obj)+'\n').encode())
			return pin(p)
		real_root=read_module((REPO/REL).parent/'split_merge/root_relay.py','B_real_validate_frame')
		self.r=types.SimpleNamespace(pin=pin,load=load,verify_pin=verify,write_new=write,validate_frame=real_root.validate_frame)
		self.st=types.SimpleNamespace(plan=self.plan,plan_pin={'path':'synthetic-plan','bytes':0,'sha256':'d'*64},
			evidence=self.e,next=adapter,r=self.r,dir=self.root,state={'phase':'merged','surviving_army_id':1},common_horizon_pin={'path':'synthetic-reviewed-helper','bytes':1,'sha256':'e'*64})
		self.live=types.SimpleNamespace(meta={'machine_id':self.rt['machine_id'],'source_head':'a'*40},binding=self.binding,
			a=types.SimpleNamespace(attempt='synthetic'),serial=0,run=self.root)
		(self.root/'requests').mkdir();(self.root/'responses').mkdir()
		self.live.request=self.request;self.st.live=self.live
		self.st.observe=self.observe;self.st.write=self.statewrite
		self.arm_rel=self.f.put('arrival-arm',self.arm);self.arm_ref={**self.arm_rel,'path':str(self.root/self.arm_rel['path'])}
		self.live.a.common_horizon=Path(h.__file__);self.live.a.common_horizon_sha256=pin(Path(h.__file__))['sha256']
		self.live.a.arrival_arm=Path(self.arm_ref['path']);self.live.a.arrival_arm_sha256=self.arm_ref['sha256']
		self.live.a.days=1;self.live.a.day_start_raw=None
	def statewrite(self,status,**extra):return self.r.write_new(self.root/'STATE.json',{'status':status,**self.st.state,**extra})
	def observe(self,name):
		ep=self.after if name.endswith('after') else self.arrival
		def absolute(p):return {**p,'path':str(self.root/p['path'])}
		frame=c.body(self.e.json(ep['snapshot']))
		command={'body':{'army_commander_candidates':{'current_commander':{'character_id':10}}}}
		p=self.f.put('current-commander',command)
		refs={'snapshot':{'response':absolute(ep['snapshot'])},'strength_raw':absolute(ep['army_result']),
			  'commanders':{'1':{'response':absolute(p)}}}
		return {'frame':frame,'packet':{'refs':refs}}
	def request(self,name,tool,args):
		self.requests.append((name,tool,args));self.live.serial+=1
		rid='synthetic-'+str(self.live.serial).zfill(3)+'-'+name
		req={'request_id':rid,'tool':tool,'arguments':args};body={}
		if name.endswith('arm'):body={'tactical_daily_sentinel':{'state':'armed','generation':3}}
		elif name.endswith('resume'):body={'accepted':True,'step':'resume-map'}
		elif name.endswith('wait'):body=c.body(self.e.json(self.after['snapshot']))
		else:
			clock=deepcopy(c.body(self.e.json(self.arm['days'][-1]['clock_source']))['clock'])
			clock.update(generation=3,starting_date_raw=1048,target_date_raw=1072,last_observed_date_raw=1072,trigger_date_raw=1072)
			body={'tactical_daily_sentinel':clock}
		res={'is_error':False,'request':req,'body':body}
		a=self.r.write_new(self.root/'requests'/(rid+'.json'),req);p=self.r.write_new(self.root/'responses'/(rid+'.json'),res)
		self.files[Path(p['path']).name]=Path(p['path']).read_bytes()
		return res,{'request':a,'response':p}
class Tests(unittest.TestCase):
	def test_connected_day_preserves_first_arrival_signed_DATA_and_natural_changes(self):
		with tempfile.TemporaryDirectory(dir=options.scratch_root) as temp:
			f=Harness(temp);old=h.time.sleep;h.time.sleep=lambda _:None
			try:ref=stage.BStages.common_horizon_stage(f.st)
			finally:h.time.sleep=old
			out=f.r.load(ref['path']);self.assertEqual(out['common_horizon']['last_day'],3)
			self.assertEqual(out['common_horizon']['first_arrival_day'],2)
			self.assertEqual(out['common_horizon']['first_arrival_endpoint'],f.arrival)
			self.assertEqual([x[0] for x in f.requests],['B-common-arm','B-common-resume','B-common-wait','B-common-status'])
			self.assertFalse(out['full_ABC_qualification']);self.assertFalse(out['military_command_submitted'])
			common=deepcopy(f.st.state['common_horizon'])
			for n in range(4,91):
				snap=f.f.edit(f.after['snapshot'],lambda v:v['body'].update(date_raw=1000+24*n))
				clock=deepcopy(c.body(f.e.json(f.arm['days'][-1]['clock_source']))['clock'])
				clock.update(generation=n,starting_date_raw=1000+24*(n-1),target_date_raw=1000+24*n,last_observed_date_raw=1000+24*n,trigger_date_raw=1000+24*n)
				cp=f.f.put('clock90',{'clock':clock})
				day={'day':n,'clock_source':cp,'paused_snapshot':snap,'strategy_army_ids':[1]}
				link=f.f.put('link90',{'qualified':True,'binding':f.binding,'plan':f.st.plan_pin,
					'arrival_arm':f.arm_ref,'day':day,'previous_complete':common['last_complete']})
				common.update(last_day=n,last_complete={**link,'path':str(Path(temp)/link['path'])})
			f.st.state['common_horizon']=common;count=len(f.requests)
			with self.assertRaisesRegex(ValueError,'D90'):h.advance(f.st,f.arm_ref)
			self.assertEqual(len(f.requests),count)
	def test_policy_D90_cohort_failure_and_claim_never_replayed(self):
		with tempfile.TemporaryDirectory(dir=options.scratch_root) as temp:
			f=Harness(temp);f.plan['post_arrival_policy']=None
			with self.assertRaisesRegex(ValueError,'frozen'):h.advance(f.st,f.arm_ref)
			self.assertEqual(f.requests,[]);f.plan['post_arrival_policy']=h.POLICY
			original=f.after['army_result'];f.after['army_result']=f.f.edit(original,lambda q:q['army_strengths'][0].update(native_carmy_id=9999))
			old=h.time.sleep;h.time.sleep=lambda _:None
			try:
				with self.assertRaises(ValueError):h.advance(f.st,f.arm_ref)
				self.assertTrue((Path(temp)/'common-day-1048.interrupted.actual.json').is_file())
				count=len(f.requests)
				with self.assertRaisesRegex(ValueError,'claim already exists'):h.advance(f.st,f.arm_ref)
				self.assertEqual(len(f.requests),count)
				f.after['army_result']=original
				h.advance(f.st,f.arm_ref,recovery_start=1048)
				self.assertEqual([x[0] for x in f.requests].count('B-common-arm'),1)
				self.assertEqual([x[0] for x in f.requests].count('B-common-resume'),1)
			finally:h.time.sleep=old
			view=adapter._view(f.arrival,f.plan,f.e,f.rt);h.signature(view)
			view['rows'][1]['regiment_replenishment_records_v1'][0]['records'][0]['persistent_regiment_id']=2**31
			with self.assertRaises(ValueError):h.signature(view)
			for invalid in (2**31,-(2**31)-1,True,None):
				ep=deepcopy(f.arrival)
				ep['army_result']=f.f.edit(ep['army_result'],lambda q:q['army_strengths'][0]['regiment_replenishment_records_v1'][0]['records'][0].update(persistent_regiment_id=invalid))
				with self.assertRaises(ValueError):adapter._view(ep,f.plan,f.e,f.rt)
if __name__=='__main__':unittest.main(argv=[sys.argv[0],*rest],verbosity=2)
