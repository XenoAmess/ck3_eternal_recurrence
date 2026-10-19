"""Three focused crosses against pinned frozen consumer AST; no runtime I/O.

All producer writes and volume/process APIs are replaced by RAM callbacks.
Actual closed metadata are read only; profile secrets and media are not read.
"""
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

import storage_canonical_compat_v1 as c

B=Path('D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep')
T=B/'robert30-v20261019-campaign01/runtime'
S=Path('D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01')
OLD=B/'p51-fresh1066-v20261019-prepare01/c22-source22-warm99/post-close/STORAGE-ADMISSION-before-C22.json'
CURRENT=S/'CURRENT-FULL-HOLDS-CANONICAL-INPUT-ACCOUNT60-SOURCE23-02.json'
OLD_SHA='60d4c4be84314f5c953c29fffa51e0d22857b1f7d211e5bae956c11835de3822'
CURRENT_SHA='88c52ab44258766bbe568f10ab0247ee5958bba28fc92689c4b80edfe9c2063c'
NOW='2026-10-19T23:30:00+00:00'
CONSUMERS={
 'supervisor':(T/'root_native29_supervisor_c16.py','2b470516f05f324440b0c23f3354109bbe67c2792339dc5a15f2166be5c3ae77'),
 'queue':(T/'root_p37c22_sdk_queue.py','20f435477beda8868c608897cfa51d459b192024e317599613613d7565c0b0cf'),
 'gate':(T/'presentation-c16/g2_saved_campaign/decision_text_admission.py','0a688fb5d974663f1228ad4263311ba0edd88d60159d4f442f51fff18cc0f872'),
 'capture':(T/'presentation-c16/ck3_obs_capture_png_retry_pause_c22.py','89e7d416bc03863b50e17a4946e77bcc35207081677b7f4f7d34374f1c97efa5'),
}


def pin(p,raw):
 return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def inputs():
 old,current=OLD.read_bytes(),CURRENT.read_bytes()
 if hashlib.sha256(old).hexdigest()!=OLD_SHA or hashlib.sha256(current).hexdigest()!=CURRENT_SHA:raise ValueError('closed input pin differs')
 policy=(Path(__file__).resolve().parents[2]/'docs/storage-retention-policy.json').read_bytes()
 return old,current,policy


def compose(old,current,policy):
 return c.compose_canonical_storage_v1(old,current,legacy_pin=pin(OLD,old),coordinator_pin=pin(CURRENT,current),policy_raw=policy,now_utc=NOW)


def source(name):
 p,sha=CONSUMERS[name];raw=p.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('actual consumer changed: '+name)
 return ast.parse(raw),str(p)


def install(node,ns,name):
 node=copy.deepcopy(node);node.name=name
 exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),ns['__file__'],'exec'),ns)
 return ns[name]


def frozen_consumers(canonical_raw):
 """RAM alias uses an existing path only for Path.resolve(strict=True)."""
 doc=json.loads(canonical_raw)
 disk=SimpleNamespace(**doc.get('disk',{'total':14000483987456,'used':13126316208128,'free':874167779328}))
 ns={'__file__':str(CONSUMERS['supervisor'][0]),'Path':Path,'N':T,'Q':T/'p37-queue',
     'read':lambda *a:doc,'shutil':SimpleNamespace(disk_usage=lambda p:disk),'admission':doc,
     'now':lambda:datetime.fromisoformat(NOW),'REPLY_RESERVE':64*1024**2,'time':__import__('time'),
     'AdmissionEnded':type('AdmissionEnded',(RuntimeError,),{}),'preserve_first_exception':lambda *a,**k:None,
     'atomic':lambda *a,**k:None}
 tree,_=source('supervisor')
 node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='guard' and n.lineno==353)
 supervisor=install(node,ns,'supervisor_guard')
 tree,filename=source('queue');qns={**ns,'__file__':filename}
 node=sorted((n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='guard'),key=lambda n:n.lineno)[0]
 node=copy.deepcopy(node);block=next(n for n in node.body if isinstance(n,ast.Try))
 cutoff=next(i for i,n in enumerate(block.body) if isinstance(n,ast.Assign) and isinstance(n.value,ast.Constant) and n.value.value=='recording_terminal_flags')
 block.body=block.body[:cutoff]+[ast.Return(value=ast.Constant(value=None))]
 queue_guard=install(node,qns,'queue_storage_guard')
 q=SimpleNamespace(next_sequence=1,admission={'review_at_utc':doc['review_at_utc']},args=SimpleNamespace(artifact_cap_bytes=2**40),artifact_bytes=lambda:0)
 tree,filename=source('capture');cns={'__file__':filename,'Path':Path,'datetime':datetime,'timezone':timezone,
     '_read':lambda *a:doc,'_sha':lambda *a:hashlib.sha256(canonical_raw).hexdigest(),
     'shutil':SimpleNamespace(disk_usage=lambda p:disk)}
 for name in ('_validate_storage','_continuous_storage','_disk_observation'):
  node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==name);install(node,cns,name)
 tree,filename=source('gate');gns={'__file__':filename,'Path':Path,'_digest':lambda *a:hashlib.sha256(canonical_raw).hexdigest(),
     'read':lambda *a:doc}
 fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='verify_segment')
 start=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='admission_path' for t in n.targets))
 end=next(i for i,n in enumerate(fn.body[start:],start) if isinstance(n,ast.If) and isinstance(n.test,ast.Call) and isinstance(n.test.func,ast.Name) and n.test.func.id=='any')
 partial=ast.FunctionDef(name='gate_storage',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=k) for k in ('n','storage','job','bound')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=copy.deepcopy(fn.body[start:end]),decorator_list=[])
 gate=install(partial,gns,'gate_storage')
 return supervisor,lambda:queue_guard(q),cns,gate


class Qualification(unittest.TestCase):
 def test_actual_full_input_preserves_schema_and_all_four_consumers(self):
  old,current,policy=inputs();raw=compose(old,current,policy);doc=json.loads(raw);legacy=json.loads(old);cap=json.loads(current)['current_capacity']
  self.assertLessEqual(len(raw),32768);self.assertLess(len(raw),len(old))
  self.assertEqual(doc['schema'],c.SCHEMA)
  for key,value in legacy.items():
   if key not in c.CURRENT_KEYS:self.assertEqual(doc[key],value,key)
  for key,value in cap.items():self.assertEqual(doc[key],value,key)
  self.assertFalse(doc['canonical_compatibility_v1']['runtime_adoption_granted_by_composer'])
  supervisor,queue,capture,gate=frozen_consumers(raw)
  supervisor();queue()
  binding=c.storage_binding_v1(raw,canonical_path=str(OLD))
  prepared=capture['_continuous_storage'](OLD,[T/'recordings'])
  self.assertEqual(prepared,binding)
  observation=capture['_disk_observation']({'recording_root':str(T),'storage':binding})
  self.assertFalse(observation['reserve_reached'])
  gate(T,binding,{'recording_root':str(T/'recordings')},{'machine_id':doc['machine_id']})
  result=c.validate_new_bundle_v1(raw,canonical_path=str(OLD),profile_storage=binding,job_storage=copy.deepcopy(binding),launch_review=doc['review_at_utc'],keeper_review=doc['review_at_utc'])
  self.assertTrue(result['compatible_only_not_runtime_grant'])

 def test_actual_prepare_card_reproduces_union_failure_not_promoted(self):
  narrow=(S/'C22-RECORDING-SOURCE32KiB-CLOSED-OBS-PROFILE64MiB-RENAME01.json').read_bytes()
  self.assertEqual(hashlib.sha256(narrow).hexdigest(),'77ba3d781ec852eae02561b5a0a41bf224b11db0730f8d960e74e6880db65d74')
  supervisor,queue,capture,gate=frozen_consumers(narrow)
  # Its local recording fields pass; that does not qualify the whole launch.
  capture['_continuous_storage'](OLD,[T/'recordings']);queue()
  with self.assertRaisesRegex(KeyError,'retained_other_reservations'):supervisor()
  with self.assertRaises(ValueError):c.storage_binding_v1(narrow,canonical_path=str(OLD))

 def test_missing_capacity_expiry_and_mixed_old_new_hashes_reject(self):
  old,current,policy=inputs();base=json.loads(current)
  for kind in ('missing_hold','false_machine','prepare_only','expired','bad_formula','missing_field','wrong_policy'):
   with self.subTest(kind=kind):
    d=copy.deepcopy(base)
    if kind=='missing_hold':del d['active_holds_source']
    elif kind=='false_machine':d['current_capacity']['machine_id']='foreign'
    elif kind=='prepare_only':d['status']='PREPARE_ONLY'
    elif kind=='expired':d['current_capacity']['review_at_utc']=d['review_at_utc']='2026-10-19T23:00:00+00:00'
    elif kind=='bad_formula':d['current_capacity']['retained_other_reservations']-=1
    elif kind=='missing_field':del d['current_capacity']['effective_project_quota']
    elif kind=='wrong_policy':d['current_capacity']['policy_version']='other'
    payload=json.dumps(d).encode()
    with self.assertRaises((ValueError,KeyError)):compose(old,payload,policy)
  raw=compose(old,current,policy);doc=json.loads(raw);binding=c.storage_binding_v1(raw,canonical_path=str(OLD))
  bad={**binding,'admission_sha256':'77ba3d781ec852eae02561b5a0a41bf224b11db0730f8d960e74e6880db65d74'}
  _,_,_,gate=frozen_consumers(raw)
  with self.assertRaisesRegex(ValueError,'Exact storage admission'):gate(T,bad,{'recording_root':str(T)},{'machine_id':doc['machine_id']})
  with self.assertRaises(ValueError):c.validate_new_bundle_v1(raw,canonical_path=str(OLD),profile_storage=binding,job_storage=bad,launch_review=doc['review_at_utc'],keeper_review=doc['review_at_utc'])
  with self.assertRaises(ValueError):c.validate_new_bundle_v1(raw,canonical_path=str(OLD),profile_storage=binding,job_storage=binding,launch_review=doc['review_at_utc'],keeper_review='old-review')


if __name__=='__main__':unittest.main(verbosity=2)
