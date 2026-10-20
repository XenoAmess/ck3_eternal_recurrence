"""A13 exact native display graph; no writes."""
from __future__ import annotations
import sys, json, hashlib, types
from pathlib import Path
OWN=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
if str(OWN) not in sys.path:sys.path.insert(0,str(OWN))
import prepare_c23_a08_display_v1 as b
import prepare_source27_a10_display_v1 as d
import prepare_a12_recording02_v1 as r
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
 out=native_capture(r.capture_source(values[CAP]))
 require((len(out),sha(out))==NATIVE,'native source pin');values[CAP]=out
 owner='presentation-c23/start_new_game_display.py'
 text=values[owner].decode()
 for a,z,n in [('len(raw)==76250','len(raw)==77036',2),(r.PIN_CAPTURE[1],NATIVE[1],3)]:text=r.swap(text,a,z,n)
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
