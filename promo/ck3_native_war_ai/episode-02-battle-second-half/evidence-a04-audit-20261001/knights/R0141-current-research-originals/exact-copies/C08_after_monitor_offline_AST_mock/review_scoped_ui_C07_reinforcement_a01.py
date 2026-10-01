from pathlib import Path
from datetime import datetime,timezone
from types import SimpleNamespace
import ast,copy,hashlib,json,sys,contextlib,io
SOURCE=Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-05-scoped-ui')
RUN=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/scoped-ui-C07-independent-review-reinforcement-a01')
RUN.mkdir(exist_ok=False)
EXPECTED='A3A31116C17E6313938677858AD230DD7945C8A8651FF16D475B14A3B1485CE5'
def identity(p):
 b=Path(p).read_bytes();return {'path':str(Path(p).resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest().upper()}
files=['scoped_ui_research_a07.py','run_paused_ui_stage_a06.py','preserve_paused_ui_checkpoint_a05.py','prepare_runtime_binding_and_plan_a07.py']
inputs=[identity(SOURCE/f)for f in files];assert inputs[0]['sha256']==EXPECTED
for f in files:
 with (RUN/f).open('xb')as out:out.write((SOURCE/f).read_bytes())
text=(SOURCE/files[0]).read_text(encoding='utf-8');tree=ast.parse(text)
names={'require','original_gui_owner_identity','verify_window','geometry_gate','stable_combat_window','original_ui','knight_hover','fit_combat_panel','monitor_payload','variable_monitor','advance'}
selected=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names]
assert {n.name for n in selected}==names
ns={'Path':Path,'datetime':datetime,'timezone':timezone,'json':json,'time':SimpleNamespace(sleep=lambda s:None),
    'identity':identity}
exec(compile(ast.Module(body=selected,type_ignores=[]),'C07 exact selected AST pure-mock-no-requests','exec'),ns)
cases=[]
def case(name,fn,reject=False):
 stdout=io.StringIO();error=None
 try:
  with contextlib.redirect_stdout(stdout):fn()
 except Exception as e:error={'type':type(e).__name__,'message':str(e)}
 passed=(error is not None)if reject else error is None
 cases.append({'name':name,'expected':'REJECT'if reject else'ACCEPT','actual':'REJECT'if error else'ACCEPT',
               'status':'PASS'if passed else'FAIL_FALSE_ACCEPT'if reject else'FAIL','error':error,'mock_stdout':stdout.getvalue()})
CONFIG={'before_date_raw':53146848,'after_date_raw':53146872,'actor_id':29829,'combat_id':16777218,'public_unit_id':18,
        'victim_id':33437,'killer_id':34120,'monitor_sequence_token':73,'managed_daily_sequence_token':74,'event_load_index':11}
VALUES={'date_raw':53146848,'revision':4,'native_revision':3,'snapshot_id':'native:3','episode_run_id':'OFFLINE-ONLY',
        'connection_generation':1,'bridge_pid':999999,'native_hello_session_generation':0,'actor':29829,'army_id':18,'paused':True}
def window(kind='combat',subject=16777218):
 return {'schema':'ck3-ingame-ui-window-v1','accepted':True,'available':True,'status':'observed','window_kind':kind,
  'window_exists':True,'effective_visible':True,'subject_id_available':True,'current_subject_id':subject,
  'date_raw':VALUES['date_raw'],'paused':True,'played_character_id':29829,'queried_revision':4,'queried_native_revision':3,
  'native_revision':3,'queried_snapshot_id':'native:3','requested_subject_id':0,'episode_run_id':'OFFLINE-ONLY',
  'queried_connection_generation':1,'dispatch_invoked':False,'verification_pending':False,'thread_id':3900,'pump_epoch':1,
  'application_owner_thread_verified':True,'gui_owner_binding_verified':True,'rng_owner_is_ui_admission_gate':False,
  'rng_owner_thread_id':0,'gui_context_address':1234,'gui_owner_address':2345,'owner_character_id':29829,
  'combat_knights_read_available':True,'hover_state_available':True,'hovered_widget_name':'left_knights',
  'hovered_ui_side':'left','hovered_combat_id':16777218,'hover_readback_is_pixels':False,'combat_roster_full_ids_available':False,
  'left_knight_count':14,'right_knight_count':27,'left_knight_breakdown':'OFFLINE MOCK fourteen','right_knight_breakdown':'OFFLINE MOCK twenty-seven',
  'tree':{'truncated':False},'combat_geometry':{'available':True,'combat_id':16777218,'coordinate_space':'native_gui_absolute',
   'stock_margin_source_verified':True,'stock_margin_source_sha256':'7FEE98B7341E21607ED3BB9089C51EF890D229DB6C16865C88133C3BA3579236',
   'readback_is_pixels':False,'full_panel_pixels_proven':False,'content_inside_viewport':True,'fit_required':False,
   'viewport':{'x':0,'y':0,'width':1920,'height':1080},'window_rect':{'x':20,'y':600,'width':875,'height':330},
   'content_union':{'x':20,'y':600,'width':875,'height':330}}}
for field in ('application_owner_thread_verified','gui_owner_binding_verified','rng_owner_is_ui_admission_gate',
              'gui_context_address','gui_owner_address','thread_id','rng_owner_thread_id'):
 for variant in ('absent','wrong-type'):
  def test(field=field,variant=variant):
   body=window()
   if variant=='absent':body.pop(field)
   else:body[field]='0'
   ns['original_gui_owner_identity'](body)
  case('owner-'+field+'-'+variant,test,True)
case('actual-RNG-zero-admitted-with-actual-GUI-owner',lambda:ns['verify_window'](window(),'combat',16777218,VALUES,CONFIG))
for key in ('current_subject_id','native_revision','queried_revision','date_raw','queried_snapshot_id','episode_run_id','paused'):
 for variant in ('absent','wrong-type'):
  def test(key=key,variant=variant):
   body=window()
   if variant=='absent':body.pop(key)
   else:body[key]=str(body[key])if type(body[key])is not str else 123
   ns['verify_window'](body,'combat',16777218,VALUES,CONFIG)
  case('window-'+key+'-'+variant,test,True)
class Mock:
 def __init__(self,body_change=None,post_owner=None,snapshot_change=None):
  self.calls=[];self.epoch=0;self.body_change=body_change;self.post_owner=post_owner;self.snapshot_change=snapshot_change;self.trace_calls=[]
 def snapshot(self,out,transport,steps,label,date):
  values=copy.deepcopy(VALUES);values['date_raw']=date
  if self.snapshot_change and'post-pixels'in label:self.snapshot_change(values)
  self.calls.append(('OFFLINE-SNAPSHOT',label));return {},{'kind':'OFFLINE MOCK'},values
 def capture(self,live,evidence,label):self.calls.append(('OFFLINE-NO-PIXELS',label));return {'kind':'OFFLINE MOCK NO PIXELS'}
 def call(self,out,label,name,params,budget):
  self.calls.append((name,label,params,budget))
  if name in ('ck3_open_character_window_v1','ck3_select_army_ui_v1','ck3_open_combat_window_v1','ck3_open_knights_window_v1','ck3_hover_combat_knights_v1','ck3_fit_combat_window_v1'):
   return {'accepted':True,'verification_pending':True}, {'kind':'OFFLINE MOCK'}
  if name=='ck3_execute_step':return {'ending_date_raw':53146872},{'kind':'OFFLINE MOCK'}
  assert name=='ck3_query_ingame_ui_window_v1'
  self.epoch+=1;body=window();body['pump_epoch']=self.epoch
  if self.body_change:self.body_change(body)
  if self.post_owner and'post-pixels'in label:self.post_owner(body)
  return body,{'kind':'OFFLINE MOCK'}
 def private_call(self,out,label,params,budget):
  self.trace_calls.append((label,params,budget))
  return {'accepted':True,'managed_daily_sequence_token':74,'status':'OFFLINE_MOCK_TRACE_PENDING'}, {'kind':'OFFLINE MOCK'}
def context(mock,label):
 directory=RUN/'cases'/label;directory.mkdir(parents=True,exist_ok=False)
 binding=directory/'bindings-OFFLINE.json';binding.write_text(json.dumps(CONFIG),encoding='utf-8')
 def write(p,v):
  with Path(p).open('x',encoding='utf-8')as f:json.dump(v,f)
 ns.update(snapshot=mock.snapshot,capture_window=mock.capture,write=write,read=lambda p:json.loads(Path(p).read_text(encoding='utf-8')))
 args=SimpleNamespace(phase='before',label=label,bindings=binding,window_kind='combat',character_role='victim',ui_side='left')
 return args,(directory,directory,directory,mock,mock)
for mode in ('original_ui','fit_combat_panel','knight_hover'):
 def positive(mode=mode):
  m=Mock();args,bound=context(m,mode+'-positive');ns[mode](args,CONFIG,bound)
  assert sum(x[0]=='OFFLINE-NO-PIXELS'for x in m.calls)==1
 case(mode+'-positive-RNG0',positive)
 for field in ('thread_id','gui_context_address','gui_owner_address'):
  def reject_owner(mode=mode,field=field):
   m=Mock(post_owner=lambda body:body.__setitem__(field,body[field]+1));args,bound=context(m,mode+'-'+field);ns[mode](args,CONFIG,bound)
  case(mode+'-post-pixels-'+field+'-drift',reject_owner,True)
 for field in ('revision','native_revision','date_raw','actor','army_id','episode_run_id','connection_generation','bridge_pid'):
  def reject_snapshot(mode=mode,field=field):
   m=Mock(snapshot_change=lambda v:v.__setitem__(field,'DRIFT'));args,bound=context(m,mode+'-snapshot-'+field);ns[mode](args,CONFIG,bound)
  case(mode+'-post-pixels-'+field+'-drift',reject_snapshot,True)
def bad_fields(body):
 for key in ('left_knight_count','right_knight_count','left_knight_breakdown','right_knight_breakdown'):body.pop(key)
def absent_hover():
 m=Mock(body_change=bad_fields);args,bound=context(m,'hover-missing-getter-fields');ns['knight_hover'](args,CONFIG,bound)
case('hover-missing-counts-and-markup-must-reject',absent_hover,True)
def invalid_hover():
 def change(b):b.update(left_knight_count=True,right_knight_count=-1,left_knight_breakdown=[],right_knight_breakdown=None)
 m=Mock(body_change=change);args,bound=context(m,'hover-invalid-getter-fields');ns['knight_hover'](args,CONFIG,bound)
case('hover-counts-and-markup-types-must-reject',invalid_hover,True)
def one_day():
 m=Mock();args,bound=context(m,'one-day-only');e=bound[2]
 for file in ('before-saved-pair.json','variable-monitor-begin.json'):(e/file).write_text('OFFLINE MOCK',encoding='utf-8')
 frame=e/'mock-frame.bin';frame.write_bytes(b'OFFLINE NO PIXELS')
 (e/'before-ui-root-review.json').write_text(json.dumps({'original_pixels_actually_reviewed':True,'reviewed_images':[identity(frame)]}),encoding='utf-8')
 ns['advance'](args,CONFIG,bound)
 assert sum(x[0]=='ck3_execute_step'for x in m.calls)==1
 assert len(m.trace_calls)==2 and'begin'in m.trace_calls[0][0]and'finish'in m.trace_calls[1][0]
 assert m.trace_calls[1][1]['expected_revision']==4
 try:ns['advance'](args,CONFIG,bound)
 except RuntimeError:pass
 else:raise AssertionError('second day accepted')
 assert sum(x[0]=='ck3_execute_step'for x in m.calls)==1 and len(m.trace_calls)==2
case('one-day-only-plus24-snapshot-before-finish-no-retry',one_day)
def monitor_token_collision():
 m=Mock();args,bound=context(m,'monitor-token-collision');args.mode='monitor-begin';config=dict(CONFIG,monitor_sequence_token=74)
 ns['variable_monitor'](args,config,bound)
case('monitor-token-independent-collision-rejected',monitor_token_collision,True)
for mutation in ('missing','duplicate','non-dict'):
 def payload_case(mutation=mutation):
  envelope={}if mutation=='missing'else{'a':{'scoped_variable_monitor':{}},'b':{'scoped_variable_monitor':{}}}if mutation=='duplicate'else{'scoped_variable_monitor':[]}
  ns['monitor_payload'](envelope)
 case('monitor-exact-one-payload-'+mutation,payload_case,True)
stage=ast.parse((SOURCE/files[1]).read_text(encoding='utf-8'))
structural={'stage_has_all_before_after_character_army_knights_combat_fit_and_two_hover_operations':all(s in(SOURCE/files[1]).read_text(encoding='utf-8')for s in ["('victim', 'killer')","('army', 'knights', 'combat')","('left', 'right')","--mode', 'fit'","--mode', 'save'"]),
 'stage_never_calls_advance_and_never_approves_pixels':'--mode\', \'advance'not in(SOURCE/files[1]).read_text(encoding='utf-8')and"'original_pixels_actually_reviewed': False"in(SOURCE/files[1]).read_text(encoding='utf-8'),
 'main_requires_monitor_before_ui_and_save':"Observe variable writers before UI/save getters"in text,
 'monitor_finish_requires_after_ui_actual_review_and_save':"After-day original pixels not reviewed"in text and"after-saved-pair.json"in text,
 'single_day_mutation_calls_in_AST':sum(isinstance(n,ast.Constant)and n.value=='life-advance'for n in ast.walk(tree))==1,
 'single_trace_finish_calls_in_AST':sum(isinstance(n,ast.Constant)and n.value=='experimental-combat-phase-event-trace-finish-v1'for n in ast.walk(tree))==1}
assert all(structural.values())
assert inputs==[identity(SOURCE/f)for f in files]
report={'kind':'INDEPENDENT_EXACT_C07_AST_MOCK_REVIEW_NOT_LIVE_OR_PIXEL_TRUTH','source_inputs':inputs,
 'script':identity(__file__),'python':sys.executable,'python_version':sys.version,'exact_AST_functions':sorted(names),
 'cases':cases,'case_count':len(cases),'passed':sum(c['status']=='PASS'for c in cases),
 'failures':[c for c in cases if c['status']!='PASS'],'structural_checks':structural,
 'source_bytes_unchanged':True,'native_requests':0,'game_or_screen_actions':0,'git_mutations':0,
 'conclusion':'C07 GUI owner/RNG0/same-frame and day guards pass; missing/invalid getter field false accepts require create-only C08 shared typed getter gate before live',
 'live_ready_for_this_C07':False,'offline_checks_do_not_close_any_mechanism':True}
with (RUN/'independent-review.json').open('x',encoding='utf-8')as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'report':identity(RUN/'independent-review.json'),'cases':len(cases),'passed':report['passed'],'failures':report['failures']},ensure_ascii=False))
