from pathlib import Path
from datetime import datetime,timezone
from types import SimpleNamespace
import ast,copy,hashlib,json,sys,contextlib,io
RUN=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/scoped-ui-C08-after-monitor-review-reinforcement-a03');RUN.mkdir(exist_ok=False)
CONSUMER=Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-05-scoped-ui/scoped_ui_research_a08.py')
HELPER=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/review_scoped_ui_C07_reinforcement_a01.py')
def identity(p):
 b=Path(p).read_bytes();return {'path':str(Path(p).resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest().upper()}
assert identity(CONSUMER)['sha256']=='169EE7EA1DBF979B3EBE0C6221A4287B908E4F0F7BFA01A14DB86AC5D671F640'
tree=ast.parse(CONSUMER.read_text(encoding='utf-8'))
names={'require','original_gui_owner_identity','original_combat_knight_fields','verify_window','geometry_gate','stable_combat_window','original_ui','knight_hover','fit_combat_panel','monitor_payload','variable_monitor'}
ns={'Path':Path,'datetime':datetime,'timezone':timezone,'json':json,'time':SimpleNamespace(sleep=lambda s:None),'identity':identity}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names],type_ignores=[]),'C08 exact selected AST no live imports','exec'),ns)
helpers=ast.parse(HELPER.read_text(encoding='utf-8'))
selected=[]
for n in helpers.body:
 if isinstance(n,ast.FunctionDef)and n.name in {'case','window','context'}:selected.append(n)
 if isinstance(n,ast.ClassDef)and n.name=='Mock':selected.append(n)
 if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id in {'CONFIG','VALUES'}for t in n.targets):selected.append(n)
cases=[]
exec(compile(ast.Module(body=selected,type_ignores=[]),'exact offline helper AST no execution branch','exec'),globals())
for mode in ('original_ui','fit_combat_panel','knight_hover'):
 def after(mode=mode):
  m=Mock(body_change=lambda b:b.update(date_raw=53146872));args,bound=context(m,mode+'-after-positive');args.phase='after'
  ns[mode](args,CONFIG,bound)
  assert sum(x[0]=='OFFLINE-NO-PIXELS'for x in m.calls)==1
 case(mode+'-after-plus24-current-paused-frame',after)
def monitor_context(label,finishing=False,failing=None):
 m=Mock();args,bound=context(m,label);args.mode='monitor-finish'if finishing else'monitor-begin';e=bound[2]
 if finishing:
  for f in ('variable-monitor-begin.json','one-day-finished.json','after-saved-pair.json'):(e/f).write_text('OFFLINE MOCK',encoding='utf-8')
  frame=e/'mock-after-frame.bin';frame.write_bytes(b'OFFLINE MOCK NO PIXELS')
  (e/'after-ui-root-review.json').write_text(json.dumps({'original_pixels_actually_reviewed':True,'reviewed_images':[identity(frame)]}),encoding='utf-8')
 def private(out,label,params,budget):
  m.trace_calls.append((label,params,budget))
  if failing=='timeout':raise TimeoutError('OFFLINE MOCK ambiguous response')
  begin='monitor-begin'in params['step']
  payload={'schema_version':1,'monitor_sequence_token':73,'character_ids':[33437,34120],'begin_date_raw':53146848,
   'failure_flags':0,'truncated':False,'whole_game_mutable_bundle_complete':False,'battle_event_causality_inferred_from_endpoint':False,
   'detours_uninstalled':not begin,'records':[{'boundary':'arm'if begin else'final_paused','failure_flags':0}]}
  return {'accepted':failing!='refused','status':'armed'if begin else'drained','body':{'scoped_variable_monitor':payload}}, {'kind':'OFFLINE MOCK'}
 m.private_call=private
 return m,args,bound
for finishing in (False,True):
 def accepted(finishing=finishing):
  m,args,bound=monitor_context('monitor-positive-'+str(finishing),finishing)
  ns['variable_monitor'](args,CONFIG,bound);assert len(m.trace_calls)==1
  params=m.trace_calls[0][1];assert params['monitor_sequence_token']==73 and params['expected_revision']==4
  assert'combat_id'not in params and'managed_daily_sequence_token'not in params
  assert('scoped_character_id'in params)==(not finishing)
  try:ns['variable_monitor'](args,CONFIG,bound)
  except RuntimeError:pass
  else:raise AssertionError('ambiguous duplicate monitor request')
  assert len(m.trace_calls)==1
 case('monitor-'+('finish'if finishing else'begin')+'-only-once-independent-token',accepted)
for failing in ('timeout','refused'):
 def failed(failing=failing):
  m,args,bound=monitor_context('monitor-finish-failure-'+failing,True,failing)
  try:ns['variable_monitor'](args,CONFIG,bound)
  except(RuntimeError,TimeoutError):pass
  else:raise AssertionError('failed monitor accepted')
  assert not(bound[2]/'variable-monitor-finish.json').exists()
  try:ns['variable_monitor'](args,CONFIG,bound)
  except RuntimeError:pass
  else:raise AssertionError('failed monitor re-sent')
  assert len(m.trace_calls)==1
 case('monitor-'+failing+'-intent-kept-no-retry',failed)
def early_finish():
 m,args,bound=monitor_context('monitor-before-after-evidence',False);args.mode='monitor-finish'
 ns['variable_monitor'](args,CONFIG,bound)
case('monitor-finish-before-required-after-artifacts-rejected',early_finish,True)
assert all(c['status']=='PASS'for c in cases),cases
for p in (CONSUMER,HELPER,Path(__file__)):
 with (RUN/p.name).open('xb')as f:f.write(p.read_bytes())
report={'kind':'ADDITIONAL_C08_AFTER_PHASE_AND_MONITOR_EXACT_AST_MOCK_NOT_NATIVE_TRUTH','source_inputs':[identity(CONSUMER),identity(HELPER)],
 'script':identity(__file__),'cases':cases,'count':len(cases),'passed':len(cases),'consumer_ready_for_root_owned_live':True,
 'no_other_case_repeated':True,'native_requests':0,'screen_actions':0,'source_or_git_mutations':0,
 'mechanisms_or_UI_pixels_closed':False,'requires_actual_root_fresh_full_DLL_eight_tests_and_offline_admission':True}
with (RUN/'independent-after-monitor-review.json').open('x',encoding='utf-8')as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'report':identity(RUN/'independent-after-monitor-review.json'),'count':len(cases),'passed':len(cases)}))
