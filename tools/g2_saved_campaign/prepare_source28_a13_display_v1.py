"""A13 exact native display graph; no writes."""
from __future__ import annotations
import sys, json, hashlib, types
from pathlib import Path

from typing import Callable, Protocol, TypedDict, cast
import re,ast
type JSONValue = None | bool | int | float | str | list[JSONValue] | dict[str,JSONValue]
type JSONObject = dict[str,JSONValue]
type Outputs = dict[Path,bytes]
class ExactRef(TypedDict):
 path: str
 bytes: int
 sha256: str

class _SourceOps(Protocol):
 def source(self,path: Path,expected: tuple[int,str]) -> tuple[bytes,ExactRef]:...
class _LegacyOps(Protocol):
 __file__: str
 def exact(self,path: Path,expected: tuple[int,str]) -> bytes:...
 def swap(self,text: str,before: str,after: str,count: int=1) -> str:...

class Recording02Plan(TypedDict):
 schema: str
 machine_id: str
 observed_at_utc: str
 display_nonce: str
 task_nonce: str
 full_storage_ref: ExactRef

def _recording02_plan(value: object, *, expected_schema: str = 'xar.A13-recording02-compose-input/v1') -> Recording02Plan:
 if type(value) is not dict:
  raise ValueError('record02 plan must be an exact object')
 obj=cast(dict[object,object],value)
 names=('schema','machine_id','observed_at_utc','display_nonce','task_nonce')
 if set(obj)!=set(names)|{'full_storage_ref'}:
  raise ValueError('record02 exact six fields required')
 strings: dict[str,str]={}
 for key in names:
  field=obj[key]
  if not isinstance(field,str) or type(field) is not str:
   raise ValueError('record02 string field: '+key)
  strings[key]=field
 raw=obj['full_storage_ref']
 if type(raw) is not dict:
  raise ValueError('record02 full exact reference object required')
 row=cast(dict[object,object],raw)
 path,size,digest=row.get('path'),row.get('bytes'),row.get('sha256')
 if (set(row)!={'path','bytes','sha256'} or not isinstance(path,str) or type(path) is not str
     or not isinstance(size,int) or type(size) is not int or not 0<size<=131072
     or not isinstance(digest,str) or type(digest) is not str or re.fullmatch('[0-9a-f]{64}',digest) is None):
  raise ValueError('record02 full reference needs exact path/int bytes/lowercase SHA')
 if not Path(path).is_absolute():
  raise ValueError('record02 full reference must be absolute')
 if strings['schema']!=expected_schema or strings['machine_id']!=MACHINE:
  raise ValueError('record02 schema or actual machine differs')
 for key in ('display_nonce','task_nonce'):
  if re.fullmatch('[0-9a-f]{32}',strings[key]) is None:
   raise ValueError('record02 finite nonce required')
 return Recording02Plan(schema=strings['schema'],machine_id=strings['machine_id'],
  observed_at_utc=strings['observed_at_utc'],display_nonce=strings['display_nonce'],
  task_nonce=strings['task_nonce'],full_storage_ref=ExactRef(path=path,bytes=size,sha256=digest))

def _recording02_ref(path: str | Path,raw: bytes) -> ExactRef:
 return ExactRef(path=str(Path(path).resolve()),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

def _recording02_json_ref(ref: ExactRef) -> JSONObject:
 return {'path':ref['path'],'bytes':ref['bytes'],'sha256':ref['sha256']}

OWN=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
if str(OWN) not in sys.path:sys.path.insert(0,str(OWN))
import prepare_c23_a08_display_v1 as b
import prepare_source27_a10_display_v1 as d
import prepare_a12_recording02_v1 as r
_src_ops=cast(_SourceOps,b)
_ops=cast(_LegacyOps,r)
require,sha,encode,pin,checked,finite=b.require,b.sha,b.encode,b.pin,b.checked,b.finite
MACHINE,O=b.MACHINE,b.O
U12=b.U8.with_name('runtime-a12')
U13=U12.with_name('runtime-a13')
TASK=O/'tasks/spec-display-a13'
INDEX=U12/'ROOT-A12-ACTUAL-CLOSURE-INDEX01.json'
INDEX_PIN=(5088,'5ad53086563d7c2d5dfa845760dd7b20f4db7511347d9d88c1b52c8a3c547d6d')
GAME=[106220,134369831434087677]
CAP='presentation-c23/ck3_obs_capture_png_retry_c23.py'
NATIVE=(77036,'a486d61435c0a50693e2d42f6769995b495e62eacaa5d7f84fa880773c902e1d')
def predecessor():
 raw,ref=b.source(INDEX,INDEX_PIN);x=json.loads(raw)
 require(x['machine_id']==MACHINE and x['SDK_status']=='SDK_NOT_STARTED' and x['game_exit_code']==1
  and x['owned_job_active_final']==0 and x['recording02_engine_exit_code']==x['recording02_publisher_exit_code']==0
  and x['NEXT']==10538 and x['unknown_10534_replayed'] is False,'actual A12 closed')
 for ref in x['closure_refs']:checked(ref)
 return [pin(INDEX,raw),*x['closure_refs']],{'66757c17b7e84c5795623621f7a7f9a3'}
PIN240=(76448,"4a7dee680da199686b62ab1d6ded9f028644ffed79b7115cbff742cbe20974b8")
PNG_HELPER="def _require_native_2560_png_v1(raw):\n    if (len(raw) < 24 or len(raw) > 8 * 1024**2\n            or not raw.startswith(b\"\\x89PNG\\r\\n\\x1a\\n\")\n            or raw[12:16] != b\"IHDR\"\n            or (int.from_bytes(raw[16:20], \"big\"), int.from_bytes(raw[20:24], \"big\")) != (2560, 1440)):\n        raise RuntimeError(\"native 2560x1440 source PNG required within finite budget\")\n\n\n"
def native_capture(raw):
    if (len(raw),hashlib.sha256(raw).hexdigest())!=PIN240:
        raise ValueError("exact 240 source")
    text=raw.decode("utf-8")
    pairs=[
      ("_require_game_client_1280_v1","_require_game_client_2560_v1",4),
      ("tuple(client_rect) != (0, 0, 1280, 720)","tuple(client_rect) != (0, 0, 2560, 1440)",1),
      ("exactly 1280x720","exactly 2560x1440",1),
      ("def _game_canvas_transform_v1():\n    return {\"positionX\": 0.0, \"positionY\": 0.0, \"alignment\": 5,\n            \"scaleX\": 2.0, \"scaleY\": 2.0, \"rotation\": 0.0,","def _game_canvas_transform_v1():\n    return {\"positionX\": 0.0, \"positionY\": 0.0, \"alignment\": 5,\n            \"scaleX\": 1.0, \"scaleY\": 1.0, \"rotation\": 0.0,",1),
      ('get_source_screenshot(name, "png", 1280, 720, -1)','get_source_screenshot(name, "png", 2560, 1440, -1)',1),
      ('def _verify_game_canvas_v1(client, scene, source, item_id, client_rect):',
       'def _verify_game_canvas_v1(client, scene, source, item_id, client_rect, *, require_native_source=True):',1),
      ('    return {key: actual[key] for key in expected}',
       '    if require_native_source and (actual.get("sourceWidth"), actual.get("sourceHeight")) != (2560, 1440):\n        raise RuntimeError("owned Game source is not native 2560x1440; upscaling forbidden")\n    return dict({key: actual[key] for key in expected}, sourceWidth=actual.get("sourceWidth"), sourceHeight=actual.get("sourceHeight"))',1),
      ('return item_id, _verify_game_canvas_v1(client, scene, source, item_id, client_rect)',
       'return item_id, _verify_game_canvas_v1(client, scene, source, item_id, client_rect, require_native_source=False)',1),
      ('def run_worker(path):',PNG_HELPER+'def run_worker(path):',1),
      ('                if len(raw) > 8 * 1024**2 or not raw.startswith(b"\\x89PNG\\r\\n\\x1a\\n"):\n                    raise RuntimeError("source PNG is malformed or exceeds its finite budget")',
       '                _require_native_2560_png_v1(raw)',1)]
    for a,b,n in pairs:
        if text.count(a)!=n:raise ValueError("native seam: "+a)
        text=text.replace(a,b,n)
    inverse=text
    for a,b,n in reversed(pairs):
        if inverse.count(b)!=n:raise ValueError("native inverse")
        inverse=inverse.replace(b,a,n)
    if inverse.encode()!=raw:raise ValueError("native inverse differs")
    out=text.encode();compile(out,"A13-capture","exec");return out
def compose(plan):
 refs,old=predecessor()
 require(plan['display_nonce'] not in old,'fresh A13 nonce')
 b.source(Path(b.__file__),d.prior.PRIOR_PIN)
 b.source(Path(r.__file__),(13471,'c1023d6af3b2e3872f0b019cf18c6ad06d86d39763566980f2c301cf079ff984'))
 patches=(
 ("spec['generation'] == 'C23-A05'","spec['generation'] == 'Source28-A12'"),
 ("spec.update(generation='C23-A06', target_runtime=str(T6), display_nonce=display_nonce)",
  "spec.update(generation='Source28-A13', target_runtime=str(T6), display_nonce=display_nonce, previous_Game_tuple=[106220,134369831434087677])"),
 ("A06_display_nonce=display_nonce","A13_display_nonce=display_nonce"),
 ("profile.pop('A05_display_nonce', None)","profile.pop('A12_display_nonce', None)"),
 ("xar.C23-A06-complete-display-RAM-review/v1","xar.Source28-A13-complete-display-RAM-review/v1"),
 ("xar.C23-A06-display-prepare-input/v1","xar.Source28-A13-display-prepare-input/v1"),
 ("spec['previous_Game_tuple'] == list(prior.OLD_GAME)","spec['previous_Game_tuple'] == [256328,134369704160368681]"),
 ("raw = finite(QUOTE5)","raw = finite(QUOTE5, 262144)"),
 ("== prior.closure.CAPTURE_SHA","== '"+r.PIN_CAPTURE[1]+"'"),
 ("profile['storage_review_at_utc'] == REVIEW_AT","profile['storage_review_at_utc'] == '2026-10-20T16:00:00+00:00'"))
 env=dict(b.recipe.__globals__,U7=U12,U8=U13,TASK8=TASK,
  QUOTE7=O/'source28-a12-prep01/A12-ROOT-QUOTE01.json',
  QUOTE7_PIN=(173639,'8d49ac6be1acbc402b028e251cb40c3791884be88b2ff32809b55f2d03602f94'),
  PROFILE7_PIN=r.PIN_PROFILE,DISPLAY7_NONCE='66757c17b7e84c5795623621f7a7f9a3',PATCHES=patches)
 ns,recipe_ref=types.FunctionType(b.recipe.__code__,env)()
 full=json.loads(checked(plan['full_storage_ref']))
 ns.update(REVIEW_AT=full['review_at_utc'],FULL5_SHA='578b0c97da972f173b242bcca558405994adfd080bc8b9e4492e1cafdbe13115')
 values,review,companions=ns['compose'](plan)
 out=hook_ready_capture(native_capture(r.capture_source(values[CAP])))
 require((len(out),sha(out))==HOOK_NATIVE,'native source pin');values[CAP]=out
 owner='presentation-c23/start_new_game_display.py'
 text=values[owner].decode()
 for a,z,n in [('len(raw)==76250','len(raw)=='+str(len(out)),2),(r.PIN_CAPTURE[1],sha(out),3)]:text=r.swap(text,a,z,n)
 values[owner]=text.encode()
 mf='presentation-c23/SOURCE-PINS-C23.json';manifest=json.loads(values[mf])
 for row in manifest['files']:
  name=row['relative_path']
  if not name.startswith('@'):row.update(pin(U13/name,values[name]))
 require(len(values)==len(manifest['files'])==18,'native18')
 values[mf]=encode(manifest)
 for name,raw in values.items():
  if name.endswith('.py'):compile(raw,name,'exec')
 review['files']=[dict(pin(U13/name,raw),relative_path=name) for name,raw in values.items()]
 review.update(changed_exact_three=None,changed_exact_four=[CAP,owner,'ROOT-DECISION-TEXT-PROVIDER-C23.json',mf],
  unchanged_source_leaves=14,source_graph_bytes=sum(map(len,values.values())),native_capture=pin(U13/CAP,out),
  actual_A12_Game_tuple=GAME,capture_live_qualified=False)
 review['inputs'].extend([*refs,recipe_ref,pin(__file__,finite(__file__)),pin(r.__file__,finite(r.__file__))])
 return values,review,companions
def build_sources(*,full_storage_ref,observed_at_utc,display_nonce,machine_id=MACHINE):
 return compose(dict(schema='xar.Source28-A13-display-prepare-input/v1',machine_id=machine_id,
  full_storage_ref=full_storage_ref,observed_at_utc=observed_at_utc,display_nonce=display_nonce))
def build_task_spec(display_values,display_review,*,task_nonce,game_launch_ref,placement_ref,bootstrap_ref,owner_contract_ref):
 fn=types.FunctionType(d.build_task_spec.__code__,dict(d.build_task_spec.__globals__,U10=U13,TASK10=TASK,GAME9=GAME,predecessor=predecessor))
 return fn(display_values,display_review,task_nonce=task_nonce,game_launch_ref=game_launch_ref,
  placement_ref=placement_ref,bootstrap_ref=bootstrap_ref,owner_contract_ref=owner_contract_ref)

# Same-Game recording02 remains independent of the frozen A13 capture.
BASE_NATIVE=NATIVE
RECORD02_GAME=(245096,134369913993181155)
HOOK_HELPERS="""def _native_obs_dimension_v1(value: object) -> int:
    if type(value) is int:
        return value
    if type(value) is float and math.isfinite(value) and value.is_integer():
        return int(value)
    raise RuntimeError("OBS source dimension must be a finite integral Number; actual=" + repr(value))


class _NativeHookPendingV1(RuntimeError):
    pass


def _wait_native_hook_v1(check: Callable[[], None]) -> None:
    deadline = time.monotonic() + 240.0
    while True:
        try:
            check()
            return
        except _NativeHookPendingV1 as error:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("owned Game hook remained 0x0 for 240s; native 2560x1440 required") from error
            time.sleep(min(.25, remaining))


"""
def hook_ready_capture(raw: bytes) -> bytes:
 require((len(raw),sha(raw))==BASE_NATIVE,'exact frozen A13 native capture')
 text=raw.decode()
 pairs=[
 ('import argparse\n','import argparse\nfrom typing import Callable\n'),
 ('def _require_game_client_2560_v1(client_rect):',HOOK_HELPERS+'def _require_game_client_2560_v1(client_rect):'),
 ('    if require_native_source and (actual.get("sourceWidth"), actual.get("sourceHeight")) != (2560, 1440):\n        raise RuntimeError("owned Game source is not native 2560x1440; upscaling forbidden")',
  '    dimensions = (_native_obs_dimension_v1(actual.get("sourceWidth")), _native_obs_dimension_v1(actual.get("sourceHeight")))\n    if require_native_source and dimensions == (0, 0):\n        raise _NativeHookPendingV1("owned Game hook not ready; actual source=0x0")\n    if require_native_source and dimensions != (2560, 1440):\n        raise RuntimeError("owned Game source must be native 2560x1440; actual=" + repr(dimensions) + "; upscaling forbidden")'),
 ('    return dict({key: actual[key] for key in expected}, sourceWidth=actual.get("sourceWidth"), sourceHeight=actual.get("sourceHeight"))',
  '    return dict({key: actual[key] for key in expected}, sourceWidth=dimensions[0], sourceHeight=dimensions[1])'),
 ('            time.sleep(2)\n            ready_frame = screenshots("before-recording")',
  '            def native_hook_check() -> None:\n                guard()\n                _output_binding(engine)\n                source_binding()\n            _wait_native_hook_v1(native_hook_check)\n            ready_frame = screenshots("before-recording")')]
 for a,z in pairs:text=_ops.swap(text,a,z)
 inverse=text
 for a,z in reversed(pairs):inverse=_ops.swap(inverse,z,a)
 require(inverse.encode()==raw,'hook changed beyond five exact seams')
 out=text.encode();compile(out,'A13-hook-ready','exec');return out

def _recording01_closure() -> list[ExactRef]:
 root=U13/'recordings/edccd0af-a9f9-42fa-91e1-53fa06b1f4be'
 failed=_ops.exact(root/'failed.json',(188,'e587ad6e234903f86e0a50bac8e39ccdffbe3b3086110664b8e8607c21343109'))
 close=_ops.exact(root/'cleanup.json',(651,'c231f7153568113a8e3cc9eadeeba1cfbf4f10d5b0656ab98ab197c3c9d1669e'))
 x=json.loads(close);c=x['engine_close']
 require(c['actual_exit_code']==0 and c['normal_exit_proven'] is True and c['forced_process_calls']==0
  and x['inputs_unbound'] is True,'old owned OBS normal closed')
 task=O/'tasks/spec-display-a13/CLOSED.json'
 pub=U13/'decision-text-publisher-c23/OWNER-CLOSED.json'
 tr,pr=finite(task),finite(pub);t,p=json.loads(tr),json.loads(pr)
 require(t['machine_id']==p['machine_id']==MACHINE and t['job_active_after_stage']==0
  and t['forced_remaining_cleanup'] is False and p['kernel_exit_observed'] is True
  and p['exit_code']==0,'old Task and publisher kernel closure')
 up=U13/'ROOT-A13-FAILED-DISPLAY01-UNREGISTER01.json'
 ur=_ops.exact(up,(2006,'90064cdbdb8c4534175afb698eb9c1b553e7556d50d46f34e543e7f85708baff'))
 ux=json.loads(ur)
 require(ux['returncode']==0 and json.loads(ux['stdout'])['actual']['absent_after'] is True,'old Task unregistered')
 return [_recording02_ref(root/'failed.json',failed),_recording02_ref(root/'cleanup.json',close),_recording02_ref(task,tr),_recording02_ref(pub,pr),_recording02_ref(up,ur)]

def compose_recording02(raw_plan: JSONObject) -> tuple[Outputs,JSONObject]:
 """Six-field create-only supplementary graph; Root alone adopts/activates."""
 plan=_recording02_plan(raw_plan)
 spec=json.loads(finite(TASK/'SPEC.json'))
 profile=json.loads(finite(U13/'ROOT-OBS-PROFILE-C23.json'))
 require(plan['display_nonce'] not in (profile['A13_display_nonce'],spec['nonce'])
  and plan['task_nonce'] not in (profile['A13_display_nonce'],spec['nonce']),'fresh record02 nonces')
 raw,_=_src_ops.source(Path(_ops.__file__),(13471,'c1023d6af3b2e3872f0b019cf18c6ad06d86d39763566980f2c301cf079ff984'))
 text=raw.decode();count=text.count('A12');text=text.replace('A12','A13')
 require(text.replace('A13','A12',count).encode()==raw,'exact generation projection')
 text=_ops.swap(text,'"len(raw)==76250"','"len(raw)==77036"')
 text=_ops.swap(text,'tasks/spec-display-a12/SPEC.json','tasks/spec-display-a13/SPEC.json')
 text=_ops.swap(text,'placement["client_rect"]==[0,0,1280,720]','placement["client_rect"]==[0,0,2560,1440]')
 text=_ops.swap(text,'old_failed_recording="d215445f-53b0-4fc9-a450-0cf29dd093c4"','old_failed_recording="edccd0af-a9f9-42fa-91e1-53fa06b1f4be"')
 ns: dict[str,object]={'__file__':str(Path(_ops.__file__)),'__name__':'_A13_record02_RAM'}
 exec(compile(text,'A13-record02-source-projection','exec'),ns)
 capture_name='ck3_obs_capture_hook240_recording02_a13.py'
 ns.update(U=U13,P=U13/'presentation-c23',TASK=O/'tasks/spec-display-a13-recording02',
  GAME=RECORD02_GAME,CAPTURE=capture_name,
  OWNER='start_new_game_display_recording02_a13.py',MANIFEST='SOURCE-PINS-A13-RECORDING02.json',
  PIN_CAPTURE=BASE_NATIVE,PIN_OWNER=(14940,'cff61633db118c6185f2e2504a1480499aec2a125b86a6f060f6275c02cb30c4'),
  PIN_MANIFEST=(6700,'b775b3b1bab526a53dafb7a610cb1df320dd4d72c0df527776ad4bf11fcc4230'),
  PIN_PROFILE=(4261,'c7749256f362c6b2b08de7f27d4653c7e7433212d261c7c6f06e21f1c1247871'),
  PIN_TASK=(3999,'ff701bf39d46c246cf8db4c5322a02aa3afd275477bba25671e81d541b204116'),
  capture_source=hook_ready_capture,prior_closure=_recording01_closure)
 fn=ns['compose']
 if not callable(fn):raise ValueError('exact composed entry is not callable')
 outputs,review=cast(Callable[[Recording02Plan],tuple[Outputs,JSONObject]],fn)(plan)
 review.update(hook_ready_budget_seconds=240,hook_ready_pending_dimensions=[0,0],
  native_source_dimensions=[2560,1440],native_scale=[1,1],frozen_A13_140_modified=False)
 review['producer']=_recording02_json_ref(_recording02_ref(__file__,finite(__file__)))
 review['old_native_capture']=_recording02_json_ref(_recording02_ref(U13/CAP,finite(U13/CAP)))
 target=U13/'presentation-c23'/capture_name
 review['new_capture']=_recording02_json_ref(_recording02_ref(target,outputs[target]))
 return outputs,review

HOOK_NATIVE=(78278,'458a747c4f1909ab8e8cf67b98d2ff2d8c6d67b1a724f170f2fb83eed3aaa1ce')

def _recording02_closure(binding_ref: ExactRef) -> list[ExactRef]:
 q=U13/'recording02-fef7eb51f5af499b94775a5ee2d6beb6'
 path=q/'publisher-binding.json'
 if (type(binding_ref) is not dict or set(binding_ref)!={'path','bytes','sha256'}
     or type(binding_ref['path']) is not str or type(binding_ref['bytes']) is not int
     or type(binding_ref['sha256']) is not str
     or binding_ref!=ExactRef(path=str(path),bytes=1029,sha256='c2c043bba29749110b81a0fed3a6fbf45f3bd1b8808e1ca56209051b974db8e2')):
  raise ValueError('explicit exact recording02 binding required')
 raw=_ops.exact(path,(1029,binding_ref['sha256']));binding=json.loads(raw)
 root=U13/'recordings/155f0795-d2c8-4027-8445-5daed7cdb6d8'
 failed=_ops.exact(root/'failed.json',(208,'1e3f9b19b94516b39442b5ca9bd028e08dff80b306ddab466053a051ab38dc28'))
 close=_ops.exact(root/'cleanup.json',(651,'612c7ff53bee8559a48899090599e3736cdd9c5dc013756ed616f0296e44a699'))
 x=json.loads(close);c=x['engine_close']
 require(x['inputs_unbound'] is True and c['normal_exit_proven'] is True and c['actual_exit_code']==0
  and c['forced_process_calls']==0,'recording02 owned OBS normal0')
 refs=_recording01_closure()+[_recording02_ref(path,raw),_recording02_ref(root/'failed.json',failed),_recording02_ref(root/'cleanup.json',close)]
 for p,e in [(q/'ROOT-NORMAL-PUBLISHER-CLOSE01.json',(1174,'7373fcd085f75ed4f37a8d4a27c66af0333e39ac388ea3fcb88d85788625c6cf')),
  (O/'tasks/spec-display-a13-recording02/CLOSED.json',(745,'3d00a9c1e8dfbcbcc897eb332cb7aa7eef8a6f9732818bf36125d7c8b1130187')),
  (U13/'ROOT-A13-FAILED-DISPLAY02-UNREGISTER01.json',(2030,'c576fceab24ae5cce469287e599b68ba5b2c3e696d8a403773288d91dc0d1972'))]:
  data=_ops.exact(p,e);refs.append(_recording02_ref(p,data))
 started_ref=binding['publisher_started'];started=json.loads(_ops.exact(Path(started_ref['path']),(started_ref['bytes'],started_ref['sha256'])))
 owner=q/'publisher/OWNER-CLOSED.json';data=finite(owner);proof=json.loads(data)
 require(all(type(v) is int for v in (started['game']['pid'],started['game']['creation_filetime'],
  started['publisher']['pid'],started['publisher']['creation_filetime'])),'strict Game/publisher identities')
 require(binding['machine_id']==proof['machine_id']==MACHINE
  and proof['publisher']==started['publisher'] and started['game']['pid']==245096
  and started['game']['creation_filetime']==RECORD02_GAME[1]
  and proof['kernel_exit_observed'] is True and proof['exit_code']==0
  and proof['forced_process_calls']==0,'recording02 actual publisher normal0')
 refs.append(_recording02_ref(owner,data))
 return refs

def compose_recording03(raw_plan: JSONObject, *, binding_ref: ExactRef) -> tuple[Outputs,JSONObject]:
 """Independent record03; consume actual record02 failure and exact binding."""
 plan=_recording02_plan(raw_plan,expected_schema='xar.A13-recording03-compose-input/v1')
 last=json.loads(finite(O/'tasks/spec-display-a13-recording02/SPEC.json'))
 require(all(value not in ('fef7eb51f5af499b94775a5ee2d6beb6',last['nonce'])
  for value in (plan['display_nonce'],plan['task_nonce'])),'fresh record03 nonces')
 tree=ast.parse(finite(__file__))
 node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='compose_recording02')
 text=ast.get_source_segment(finite(__file__).decode(),node)
 if text is None:raise ValueError('record02 source function absent')
 pairs=[
  ('def compose_recording02(','def _recording03_recipe('),
  ('plan=_recording02_plan(raw_plan)',"plan=_recording02_plan(raw_plan,expected_schema='xar.A13-recording03-compose-input/v1')"),
  (" ns: dict[str,object]=",''' original=text
 count=text.count('recording02');text=text.replace('recording02','recording03')
 require(text.replace('recording03','recording02',count)==original,'exact record03 namespace')
 original=text
 count=text.count('RECORDING02');text=text.replace('RECORDING02','RECORDING03')
 require(text.replace('RECORDING03','RECORDING02',count)==original,'exact record03 generation')
 ns: dict[str,object]='''),
  ('spec-display-a13-recording02','spec-display-a13-recording03'),
  ('ck3_obs_capture_hook240_recording02_a13.py','ck3_obs_capture_hook240_recording03_a13.py'),
  ('start_new_game_display_recording02_a13.py','start_new_game_display_recording03_a13.py'),
  ('SOURCE-PINS-A13-RECORDING02.json','SOURCE-PINS-A13-RECORDING03.json'),
  ('old_failed_recording="edccd0af-a9f9-42fa-91e1-53fa06b1f4be"','old_failed_recording="155f0795-d2c8-4027-8445-5daed7cdb6d8"')]
 for before,after in pairs:text=_ops.swap(text,before,after)
 inverse=text
 for before,after in reversed(pairs):inverse=_ops.swap(inverse,after,before)
 original=ast.get_source_segment(finite(__file__).decode(),node)
 require(inverse==original,'record03 function changed outside exact seams')
 def closure() -> list[ExactRef]:
  return _recording02_closure(binding_ref)
 scope: dict[str,object]=dict(globals());scope['_recording01_closure']=closure
 exec(compile(text,'A13-record03-RAM-recipe','exec'),scope)
 fn=scope['_recording03_recipe']
 if not callable(fn):raise ValueError('record03 recipe not callable')
 return cast(Callable[[JSONObject],tuple[Outputs,JSONObject]],fn)(raw_plan)
