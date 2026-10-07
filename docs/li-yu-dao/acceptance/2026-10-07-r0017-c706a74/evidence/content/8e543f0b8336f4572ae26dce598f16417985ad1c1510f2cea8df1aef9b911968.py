from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
B=Path('C:/workspace/ck3_lyd_runtime_20261004');O=Path(__file__).parent;RUN=B/'live-attempt-017';S=B/'r17-root-bound-close-source-20261007-002'
P='C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe'
def ref(p):
 b=p.read_bytes();return {'path':p.resolve().as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def load(p):return json.loads(p.read_bytes())
def need(ok,msg):
 if not ok:raise ValueError(msg)
def put(n,v):
 p=O/n
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
 return ref(p)
inputs={
 'original_handle_observation':ref(RUN/'mcp-client-001/0025-r17-027-normal-exit-observe.sdk-result.json'),
 'original_native_observation':ref(RUN/'mcp-client-001/0025-r17-027-normal-exit-observe.native-01.json'),
 'process_absence':ref(O/'ACTUAL-PROCESS-ABSENCE.json'),
 'release_receipt':ref(B/'r17-root-screen-release-20261007-001/RELEASE.actual.json'),
 'after_list':ref(B/'r17-root-screen-release-20261007-001/BUS-AFTER-RELEASE.parsed.json'),
 'original_holder_process_result':ref(B/'r17-original-exec-completion-20261007-001/HOLDER-ORIGINAL-EXEC.actual.json'),
 'original_keeper_process_result':ref(B/'r17-original-exec-completion-20261007-001/KEEPER-ORIGINAL-EXEC.actual.json')}
need(set(inputs)=={'original_handle_observation','original_native_observation','process_absence','release_receipt','after_list','original_holder_process_result','original_keeper_process_result'},'Exact existing seven refs required')
for key,pid,ctime,session in [('original_holder_process_result',14208,1791333766.1629004,45013),('original_keeper_process_result',20436,1791332451.9545596,39989)]:
 row=load(Path(inputs[key]['path']))
 need(set(row)=={'schema','tool_session_id','expected_pid','expected_create_time','raw_tool_result','reopened_process'} and row['schema']=='lyd.original-exec-process-completion.v1' and (row['tool_session_id'],row['expected_pid'],row['expected_create_time'])==(session,pid,ctime) and row['reopened_process'] is False,'Exact original completion wrapper facts differ')
 need(type(row['raw_tool_result']['exit_code']) is int and row['raw_tool_result']['exit_code']==0 and type(row['raw_tool_result']['output']) is str,'Actual original tool completion zero required')
native=load(Path(inputs['original_native_observation']['path']));result=native['result']
need(result['typed_normal_exit_observed'] is False and result['native_observation'] is None and result['status']=='process_exit_observed_zero','Honest actual untyped process exit must remain unchanged')
absence=load(Path(inputs['process_absence']['path']));need(absence['same_original_identities_absent'] is True and absence['no_current_managed_game_or_native_services'] is True,'Actual postrelease absence incomplete')
request=put('ROOT-BOUNDARY-INPUTS.actual.json',inputs)
target=B/'r17-actual-closed-boundary-20261007-001';need(not target.exists(),'Root boundary output must be fresh; choose new attempt if it exists')
author=ref(S/'author_closed_boundary.py');verifier=ref(S/'verify_previous_boundary.py');guard=ref(S/'guarded_helper_close.py')
base=[P,'-B',author['path'],'--request',request['path'],'--sha256',request['sha256']]
argv=put('ROOT-AUTHOR-ARGV.actual.json',{'author_source':author,'verifier_source':verifier,'guard_source':guard,'request':request,'check':base+['--check'],'create':base+['--create','--output',target.as_posix()],'root_execution_only':True,'executed_by_this_author':False,'future_actual_review_path':str(target/'PREVIOUS-BOUNDARY.actual.json'),'future_actual_review_ref':None})
support=[]
for p in [B/'r17-root-client-execution-20261007-001/RESULT.actual.json',B/'r17-root-keeper-execution-20261007-001/RESULT.actual.json',RUN/'root-holder-execution-002/RESULT.actual.json',B/'r17-retained-helper-handles-20261007-001/capture-001/EXIT-client.actual.json',B/'r17-retained-helper-handles-20261007-001/capture-001/EXIT-keeper.actual.json',B/'r17-retained-helper-handles-20261007-001/capture-001/FINAL.actual.json',B/'screen-lease-live-r0017/FINAL.json',RUN/'mcp-client-001/session-closed.json',RUN/'mcp-client-001/0024-r17-026-normal-exit-confirm-desktop.native-01.json']:
 support.append(ref(p))
manifest=put('ACTUAL-CLOSURE-SOURCE-REFS.json',{'inputs':inputs,'supporting_actual_refs':support,'typed_normal_exit_observed':False,'terminal_native_ack_observed':False,'normal_exit_callback_verified':False,'game_original_HANDLE_exit0_observed':True,'source_head':'c706a74f9d00dd842b7edce8901fb3417344fd9c','business_GREEN':False,'formal_PASS':None,'autosave_verified':False,'new_boundary_authored_here':False})
index=put('INDEX.json',{'status':'ACTUAL_POSTRELEASE_ABSENCE_AND_SEVEN_REF_REQUEST_READY_ROOT_AUTHOR_NOT_EXECUTED','request':request,'root_argv':argv,'source_refs':manifest,'author':author,'verifier':verifier,'guard':guard,'actual_process_absence':inputs['process_absence'],'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'files':[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='INDEX.json'],'SDK_calls':0,'game_actions':0,'bus_calls':0,'process_mutations':0,'main_writes':0,'business_GREEN':False,'typed_normal_exit_observed':False})
print(json.dumps({'request':request,'root_argv':argv,'index':index,'support':support,'inputs':inputs},ensure_ascii=False,indent=2))
