from pathlib import Path
import argparse,ast,copy,hashlib,importlib.util,json,subprocess,sys
sys.dont_write_bytecode=True
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004');OLD=BASE/'r17-root-bound-close-source-20261007-001';OUT=Path(__file__).parent
PY='C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe'
CLIENT=BASE/'live-attempt-017/mcp-client-001'
SDK=CLIENT/'0025-r17-027-normal-exit-observe.sdk-result.json';NATIVE=CLIENT/'0025-r17-027-normal-exit-observe.native-01.json'
def need(ok,msg):
 if not ok:raise ValueError(msg)
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':p.resolve().as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def put(n,v):
 p=OUT/n
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
def create(n,raw):
 p=OUT/n
 with p.open('xb') as f:f.write(raw)
 return ref(p)
def replace_once(text,old,new):
 need(text.count(old)==1,'Unique sealed source delta required')
 return text.replace(old,new,1)
g=(OLD/'guarded_helper_close.py').read_text(encoding='utf-8-sig')
helper='''def game_exit_observation_limits(result):
    typed = result['typed_normal_exit_observed']
    need(type(typed) is bool, 'Actual typed observation must remain an exact boolean')
    if typed is False:
        need(result['schema'] == 'ck3-normal-exit-process-observation-result-v1' and result['native_observation'] is None and result['driver_dispatch_receipt_observed_monotonic_ns'] is None and result['native_submission_count'] == 0, 'Untyped closure admits only the existing read-only original-HANDLE observer with missing terminal native ACK; no semantic callback credit')
    return {'typed_normal_exit_observed': typed, 'terminal_native_ack_observed': result['native_observation'] is not None, 'normal_exit_callback_verified': typed, 'closure_credit': 'ORIGINAL_PROCESS_HANDLE_EXIT0_ONLY' if not typed else 'TYPED_NORMAL_EXIT_AND_ORIGINAL_PROCESS_HANDLE_EXIT0'}

'''
g=replace_once(g,'def game_exit(args, values):',helper+'def game_exit(args, values):')
g=replace_once(g,"native['status'] == result['status'] == 'process_exit_observed_zero' and result['typed_normal_exit_observed'] is True and", "native['status'] == result['status'] == 'process_exit_observed_zero' and")
g=replace_once(g,"'Actual typed normal original game HANDLE exit0 required; no retry or autosave credit'", "'Actual original game HANDLE exit0 required; preserve typed/native ACK limits and grant no retry or autosave credit'")
g=replace_once(g,"    return {'game_sdk': sdk_ref,", "    limits = game_exit_observation_limits(result)\n    return {**limits, 'game_sdk': sdk_ref,")
gr=create('guarded_helper_close.py',g.encode('utf-8'))
v=(OLD/'verify_previous_boundary.py').read_text(encoding='utf-8-sig')
v=replace_once(v,"'game_original_HANDLE_exit0_observed': True,", "'game_original_HANDLE_exit0_observed': True, 'typed_normal_exit_observed': game['typed_normal_exit_observed'], 'terminal_native_ack_observed': game['terminal_native_ack_observed'], 'normal_exit_callback_verified': game['normal_exit_callback_verified'], 'closure_credit': game['closure_credit'],")
vr=create('verify_previous_boundary.py',v.encode('utf-8'))
ar=create('author_closed_boundary.py',(OLD/'author_closed_boundary.py').read_bytes())
deps=json.loads((OLD/'DEPENDENCIES.json').read_bytes());deps['guarded_close_source']=gr;dr=put('DEPENDENCIES.json',deps)
create('FUTURE-BOUNDARY-INPUTS.pending.json',(OLD/'FUTURE-BOUNDARY-INPUTS.pending.json').read_bytes())
def module(p,name):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
oldmod=module(OLD/'guarded_helper_close.py','r17_old_guard_focused')
newmod=module(OUT/'guarded_helper_close.py','r17_new_guard_focused')
args=argparse.Namespace(game_sdk=SDK,game_sdk_sha256=ref(SDK)['sha256'],game_native=NATIVE,game_native_sha256=ref(NATIVE)['sha256'])
values,pins=newmod.fixed()
try:
 oldmod.game_exit(args,values)
 raise AssertionError('Old typed-true guard unexpectedly accepted this actual observer')
except ValueError as e:
 need('Actual typed normal original game HANDLE exit0 required' in str(e),'Expected exact old rejection only')
 put('SOURCE001-ACTUAL-REJECTION.json',{'source':ref(OLD/'guarded_helper_close.py'),'SDK':ref(SDK),'native':ref(NATIVE),'error':'ValueError: '+str(e),'actions':0})
fact=newmod.game_exit(args,values)
need(fact['typed_normal_exit_observed'] is False and fact['terminal_native_ack_observed'] is False and fact['normal_exit_callback_verified'] is False and fact['closure_credit']=='ORIGINAL_PROCESS_HANDLE_EXIT0_ONLY','No typed relabel allowed')
result=json.loads(NATIVE.read_bytes())['result']
contract=sys.modules['normal_exit_contract_v1']
negatives=[]
for name,mut in [
 ('changed_retained_token',lambda x:x['process_observation'].__setitem__('retained_handle_token','0'*32)),
 ('changed_FILETIME',lambda x:x['process_observation'].__setitem__('creation_filetime_100ns',x['process_observation']['creation_filetime_100ns']+1)),
 ('nonzero_exit',lambda x:x['process_observation'].__setitem__('exit_code',7)),
 ('unsignaled_wait',lambda x:x['process_observation'].__setitem__('wait_result',258)),
 ('typed_true_without_native',lambda x:x.__setitem__('typed_normal_exit_observed',True)),
 ('retry_true',lambda x:x.__setitem__('retry_authorized',True)),
 ('autosave_true',lambda x:x.__setitem__('autosave_verified',True)),
 ('resubmitted_observer',lambda x:x.__setitem__('native_submission_count',1)),
 ('unknown_typed_none',lambda x:x.__setitem__('typed_normal_exit_observed',None)),
 ('terminal_request_false_shape',lambda x:x.__setitem__('schema','ck3-normal-exit-request-result-v1')),
]:
 candidate=copy.deepcopy(result);mut(candidate)
 try:
  contract.normalize_public_exit_observation_result(candidate);newmod.game_exit_observation_limits(candidate)
 except (ValueError,KeyError,TypeError) as e:negatives.append({'case':name,'rejected':True,'error':type(e).__name__+': '+str(e)})
 else:raise AssertionError('Malformed original exit accepted: '+name)
checks=[]
for p in [OUT/'guarded_helper_close.py',OUT/'verify_previous_boundary.py',OUT/'author_closed_boundary.py']:
 ast.parse(p.read_bytes())
 run=subprocess.run([PY,'-B',str(p),'--help'],capture_output=True)
 create(p.stem+'.help.stdout',run.stdout);create(p.stem+'.help.stderr',run.stderr)
 need(run.returncode==0,'Source help failed')
 checks.append({'source':ref(p),'AST':True,'help_exit_code':run.returncode})
focused=put('FOCUSED-ACTUAL-GAME-EXIT.json',{'status':'ACTUAL_ORIGINAL_HANDLE_EXIT0_FALSE_TYPED_PRESERVED','actual_fact':fact,'pins':pins,'negative_cases':negatives,'source_checks':checks,'SDK_callbacks':0,'game_actions':0,'helper_close_actions':0,'bus_calls':0,'OpenProcess_calls':0,'main_writes':0,'future_client_exit0':None,'future_keeper_exit0':None,'future_CAS_release':None})
common=['--game-sdk',str(SDK),'--game-sdk-sha256',ref(SDK)['sha256'],'--game-native',str(NATIVE),'--game-native-sha256',ref(NATIVE)['sha256']]
argv={'check_game_exit':[PY,'-B',str(OUT/'guarded_helper_close.py'),'check-game-exit',*common],
      'close_client_ROOT_only':[PY,'-B',str(OUT/'guarded_helper_close.py'),'close-client',*common,'--execute-root-authorized','--output',str(BASE/'r17-root-client-close-20261007-001')],
      'stop_keeper_ROOT_only':[PY,'-B',str(OUT/'guarded_helper_close.py'),'stop-keeper',*common,'--execute-root-authorized','--output',str(BASE/'r17-root-keeper-stop-20261007-001')],
      'release_screen_ROOT_only':[PY,'-B',str(OUT/'guarded_helper_close.py'),'release-screen',*common,'--execute-root-authorized','--output',str(BASE/'r17-root-screen-release-20261007-001')],
      'author_closed_check':[PY,'-B',str(OUT/'author_closed_boundary.py'),'--request',None,'--sha256',None,'--check'],
      'actual_future_closure_inputs':'Only ROOT actual Client/keeper original retained HANDLE0 + holder/keeper original-exec completion wrappers0 + CAS release/after-list/absence can fill the pending seven-ref request; NULL rejects',
      'executed_by_this_author':False}
argvref=put('ROOT-ARGV.actual-game-inputs.json',argv)
index={'status':'ACTUAL_GAME_ORIGINAL_HANDLE_EXIT0_BOUND_SOURCE_ONLY_HELPER_CLOSURE_PENDING','previous_source_index':ref(OLD/'INDEX.json'),'guarded_close_source':gr,'verifier':vr,'closed_boundary_author':ar,'dependencies':dr,'focused_actual_check':focused,'root_argv':argvref,'source_revision':newmod.HEAD,'run_root':str(newmod.RUN),'root_screen_task':newmod.TASK,'typed_normal_exit_observed':False,'terminal_native_ack_observed':False,'normal_exit_callback_verified':False,'game_original_HANDLE_exit0_observed':True,'business_GREEN':False,'autosave_verified':False,'future_client_exit0':None,'future_keeper_exit0':None,'future_CAS_release':None,'all_mutation_actions':0}
ir=put('INDEX.json',index)
print(json.dumps({'index':ir,'guard':gr,'verifier':vr,'author':ar,'game_inputs':{'SDK':ref(SDK),'native':ref(NATIVE)},'focused':focused,'argv':argvref},ensure_ascii=False,indent=2))
