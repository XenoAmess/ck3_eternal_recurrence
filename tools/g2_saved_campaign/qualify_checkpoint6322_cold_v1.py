"""One closed positive and exact negatives, plus original-source AST scope."""
from pathlib import Path
import ast
import copy
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
sys.dont_write_bytecode = True
ROOT = Path('Z:/ck3_mod_rewrite')
sys.path.insert(0, str(ROOT/'tools/g2_saved_campaign'))
from prepare_checkpoint6322_cold_v1 import build_sources, T, port, text, C14
from checkpoint6322_cold_contract_v1 import project_saved_frontier, validate_rollback, validate_abnormal_closure

P = T.parent.parent/'p51-fresh1066-v20261019-prepare01'
F = P/'c13-auto6356-failure88/display-closed'
def pin(p):
    raw = Path(p).read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):
    return json.loads(Path(p).read_bytes())
admission = {key:pin(p) for key,p in {
    'original_state': P/'c14-war6356-warm88/clean/ROOT-CUMULATIVE-LOOP-STATE.json',
    'original_governance': P/'c14-war6356-warm88/clean/ROOT-GOVERNANCE-RESULT-STATE.json',
    'rollback_frontier': F/'CHECKPOINT6322-FRONTIER.json',
    'save_response': T/'p37-responses/6322-1-result.json',
    'saved_semantic_response': T/'p37-responses/6321-1-result.json'}.items()}
cadence = T/'root_p37_checkpoint_cadence.py'
require_pin = pin(cadence)
if require_pin['sha256'] != 'a017eded18ca03733700fd61b10cace8981e5379e73dbe99b4d281fb97e4ae87':
    raise ValueError('different frozen cadence')
tree = ast.parse(cadence.read_bytes())
callback = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='checkpoint_saved')
scope={'STATE_KEY':'checkpoint_calendar_v1','_scope':lambda f:{k:f.get(k) for k in ('actor_character_id','episode_run_id')}}
exec(compile(ast.fix_missing_locations(ast.Module(body=[callback],type_ignores=[])), str(cadence),'exec'),scope)
old = read(admission['original_state']['path'])
seed, gov = project_saved_frontier(admission, checkpoint_saved=scope['checkpoint_saved'])
assert old == read(admission['original_state']['path'])
assert seed['completed_cycles']==3023 and seed['counts']['checkpoint_saved']==35
assert seed['before']['date_raw']==53202384 and seed['checkpoint_dirty_since_save'] is False
assert seed['start_date_raw']==old['start_date_raw'] and seed['campaign_goal_anchor']==old['campaign_goal_anchor']
assert seed['checkpoint_calendar_v1']['war_ids'] is None
validate_rollback(admission,seed,gov,checkpoint_saved=scope['checkpoint_saved'])
neg=[]
for label,mutate in (
    ('future_live_date',lambda s,g:s['before'].update(date_raw=53202696)),
    ('future_counts',lambda s,g:s.update(counts=old['counts'])),
    ('wrong_governance_frontier',lambda s,g:g.update(completed_cycles=3037))):
    s,g=copy.deepcopy(seed),copy.deepcopy(gov); mutate(s,g)
    try: validate_rollback(admission,s,g,checkpoint_saved=scope['checkpoint_saved'])
    except ValueError: neg.append(label)
    else: raise AssertionError(label)
close={'old_Game':{'pid':15512,'creation_filetime':134368811928524228},
    'checkpoint':read(T/'p37-responses/6322-1-result.json')['result']['structured_content']['checkpoint'],
    'abnormal_display_closure':pin(F/'FROZEN.json'),
    'abnormal_supervisor_closure':pin(F/'GAME-SUPERVISOR-EXIT-FROZEN.json'),
    'sidecars':[pin(P/'c14-war6356-warm88/clean'/name) for name in (
        'faction-gift-pending-v1.json','active-scheme-sway-formal-private-v1.json','ordinary-sway-schedule-v1.json')]}
closure=validate_abnormal_closure(close)
bad=copy.deepcopy(close); bad['old_Game']['pid']=15513
try: validate_abnormal_closure(bad)
except ValueError: neg.append('wrong_old_Game')
else: raise AssertionError('wrong physical generation')
files=build_sources()
queue=ast.parse(files['root_p37c15_sdk_queue.py'])
current=[('P37C14','P37C15'),('p37c14','p37c15'),('adoption_c14','adoption_c15'),('-C14','-C15'),('SDKC14','SDKC15')]
physical=[('_c11','_c15'),('-C11','-C15')]
expected=ast.parse(port(text(T/C14['queue'][0],C14['queue'][1]),current+physical))
def classes(t):
    return {n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,ast.ClassDef)}
assert classes(queue)==classes(expected)
# Caller, original loop, guarded main and all classes remain unchanged; only
# the bottom warm/cold factory, names and already-read timing getter differ.
def functions(t):
    return {n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
assert functions(queue)==functions(expected)
for name,raw in files.items():
    compile(raw,name,'exec')
out={'schema':'xar.c15.checkpoint6322-software-qualification/v1','machine_id':'xenoamess-full-tower-eb9d2c1186',
    'observed_at_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS_SOURCE_ONLY',
    'positive':'real closed6322 frontier and exact abnormal closure','negatives_rejected':neg,
    'seed_restored_cycles':3023,'seed_restored_date_raw':53202384,'checkpoint_saved_count':35,
    'historical_later_cycles':3037,'historical_later_date_raw':53202696,
    'original_snapshot_claimed':False,'original_classes_and_top_functions_AST_equal_after_namespace':True,
    'files':[{'basename':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for name,raw in files.items()],
    'source_bytes':sum(map(len,files.values())),'Driver_SAVE_bodies_or_process_calls':0,
    'future_actual_constructor_SEM_CAP_not_claimed':True,'abnormal_closure':closure}
path=ROOT/'_runtime/c15-checkpoint6322-source-qualification88.json'
with path.open('x',encoding='utf8') as stream: json.dump(out,stream,ensure_ascii=False,indent=2); stream.write('\n')
print(json.dumps(pin(path)))
