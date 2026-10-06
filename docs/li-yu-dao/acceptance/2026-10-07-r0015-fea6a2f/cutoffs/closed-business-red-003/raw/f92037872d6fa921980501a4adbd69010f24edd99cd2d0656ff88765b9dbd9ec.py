"""Genuine R15 v3 closure source; no SDK/game/signals/lease/process lookup."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,importlib.util,sys,argparse
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004').resolve()
RUN=BASE/'live-attempt-015'
HEAD='fea6a2f9f7233f2e3bab6cdd1329b55aa09ca17c'
TASK='ck3-lyd-r15-formal-20261007-001'
KEYS={'schema','status','source_head','root_screen_task','original_process','launch','original_handle_observation','original_native_observation','helpers_closed','process_absence','keeper_final','release_receipt','after_list','consumer_closed','consumer_session','consumer_close_result'}
INPUTS={'original_handle_observation','original_native_observation','process_absence','release_receipt','after_list','original_holder_process_result','original_keeper_process_result'}
def need(ok,message):
 if not ok:raise ValueError(message)
def same(a,b):return Path(a).resolve()==Path(b).resolve()
def stamp(value):
 d=datetime.fromisoformat(value.replace('Z','+00:00'));need(d.tzinfo is not None,'Aware actual timestamp required');return d
def byte_ref(p):
 p=Path(p);need(p.is_absolute(),'Absolute actual path required')
 for q in (p,*p.parents):need(not q.is_symlink() and not q.is_junction(),'Linked input refused')
 need(p.suffix.lower()!='.ck3','Save body reads forbidden')
 raw=p.read_bytes();return raw,{'path':p.resolve().as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def verify_byte_ref(row):
 need(type(row) is dict and set(row)=={'path','bytes','sha256'},'Non-NULL complete actual ref3 required')
 raw,actual=byte_ref(row['path']);need(actual['bytes']==row['bytes'] and actual['sha256']==row['sha256'].lower(),'Actual byte/SHA changed')
 return raw
def read_ref(row):return json.loads(verify_byte_ref(row))
def dependencies():return json.loads((HERE/'DEPENDENCIES.json').read_bytes())
def load_guard():
 row=dependencies()['guarded_close_source'];verify_byte_ref(row)
 spec=importlib.util.spec_from_file_location('r15_original_handle_close_guard',row['path'])
 module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
 return module
def validate_process_results(helpers,capture):
 expected={'holder':(47805,capture['holder_pid'],capture['holder_create_time']),'keeper':(65664,19880,1791313373.0698714)}
 rows=helpers['original_process_results'];need(set(rows)==set(expected),'Original holder and keeper exec process completions required')
 for role,(session,pid,ctime) in expected.items():
  item=rows[role]
  need(set(item)=={'session_id','pid','create_time','result'} and (item['session_id'],item['pid'],item['create_time'])==(session,pid,ctime),'Original exec session/identity differs')
  raw=read_ref(item['result'])
  need(type(raw) is dict and type(raw.get('exit_code')) is int and raw['exit_code']==0 and type(raw.get('output')) is str,'Original tools.write_stdin final completion exit0 required')
  if 'session_id' in raw:need(raw['session_id']==session,'Original session result id differs')
 return {role:rows[role]['result'] for role in rows}
def verify_decoded_review(review,data):
 need(set(review)==KEYS and review['schema']=='lyd.root.previous-cold-boundary-review.v3' and review['status']=='ROOT_REVIEWED_ACTUAL_CLOSED_RELEASED_BOUNDARY','Existing v3 16 fields/status required')
 need(review['source_head']==HEAD and review['root_screen_task']==TASK,'Genuine current R15 source/task required; R14 rejected')
 deps=dependencies();guard=load_guard();values,pins=guard.fixed()
 process=review['original_process'];launch=data['launch'];session=data['consumer_session']
 need(set(process)=={'pid','process_create_time','process_creation_filetime_100ns'} and process['pid']==14452 and process['process_create_time']==1791313780.8972144,'Original R15 game identity differs')
 need(review['launch']==deps['launch'] and review['consumer_session']==deps['consumer_session'],'Original launch/session byte refs required')
 need(launch['game_started'] is True and launch['status']=='GAME_CREATED_REQUIRES_NATIVE_LOAD_READBACK' and launch['source_revision']==HEAD and launch['pid']==process['pid'] and launch['process_create_time']==process['process_create_time'],'Actual launch identity differs')
 sdkrow=review['original_handle_observation'];natrow=review['original_native_observation']
 args=argparse.Namespace(game_sdk=Path(sdkrow['path']),game_sdk_sha256=sdkrow['sha256'],game_native=Path(natrow['path']),game_native_sha256=natrow['sha256'])
 game=guard.game_exit(args,values)
 need(game['game_sdk']==sdkrow and game['game_native']==natrow,'Actual SDK/native descriptors differ')
 native=data['original_native_observation'];result=native['result'];observed=result['process_observation'];before=result['process_preconfirm_pin']
 need(observed['creation_filetime_100ns']==before['creation_filetime_100ns']==process['process_creation_filetime_100ns'],'Original game FILETIME differs')
 need(session['client_session_id']=='3752b80510144540a5ff173194ab5bb8' and native['session_id']=='de4469c9251145468e0ca685176cbc8f','Original separate SDK/native sessions differ')
 helpers=data['helpers_closed'];facts=guard.keeper_closed(values)
 need(set(helpers)=={'results','original_capture','retained_holder_final','original_process_results'} and helpers['results']==facts['helpers_closed_value']['results'],'Original helper row bytes/derived READY source differ')
 need(helpers['original_capture']==deps['original_capture'] and helpers['retained_holder_final']==facts['retained_holder_final'],'Original capture/holder FINAL refs differ')
 for k in ('consumer_closed','consumer_close_result','keeper_final'):
  need(review[k]==facts[k],'Original current helper closure ref differs: '+k)
 process_results=validate_process_results(helpers,values['capture'])
 final=data['keeper_final'];release=data['release_receipt']
 need(release['schema']=='codex.task_bus.v1' and release['ok'] is True and release['task']['task_id']==release['event']['task_id']==TASK and release['task']['resources']==release['event']['resources']==[] and release['task']['state']=='done' and release['task']['last_sequence']==release['event']['sequence'] and release['event']['sequence']>final['last_sequence'],'Actual final CAS done/released required')
 listed=data['after_list']
 need(listed['schema']=='codex.task_bus.v1' and listed['ok'] is True and type(listed['tasks']) is list and not any('ck3-screen:acquired' in r['resources'] for r in listed['tasks']),'Actual screen vacancy required')
 own=[r for r in listed['tasks'] if r['task_id']==TASK]
 need(len(own)==1 and own[0]['resources']==[] and own[0]['state']=='done' and own[0]['last_sequence']==release['event']['sequence'],'After-list must retain actual released R15 task')
 absent=data['process_absence']
 need(absent['same_original_identities_absent'] is True and absent['no_current_managed_game_or_native_services'] is True and absent['remaining_managed_game_or_native_services']==[] and all(r['same_original_identity_alive'] is False for r in absent['original_identities']),'Actual post-release process absence required; never exit0 substitute')
 identities={r['role']:r for r in absent['original_identities']}
 expected={'game':(14452,1791313780.8972144),'client':(9624,1791316076.4627192),'keeper':(19880,1791313373.0698714),'holder':(14760,1791316356.256702)}
 need(all(role in identities and (identities[role]['pid'],identities[role]['create_time'])==value for role,value in expected.items()),'Actual original four process absence identities differ')
 need(stamp(absent['observed_at_utc'])>=stamp(release['event']['timestamp_utc']),'Absence predates actual release')
 return {'actual_prior_identity':process,'actual_prior_source_head':HEAD,'actual_prior_task':TASK,
  'actual_original_exec_process_results':process_results,
  'actual_exit_observation_limits':{'game_original_HANDLE_exit0_observed':True,'client_exit_code':0,'keeper_exit_code':0,'client_OS_exit0_observed':True,'keeper_OS_exit0_observed':True,'holder_original_exec_process_exit0_observed':True,'holder_original_exec_session_id':47805,'keeper_original_exec_session_id':65664,'native_session_id':native['session_id'],'consumer_session_id':session['client_session_id'],'autosave_verified':False}}
def verify_previous_boundary_v3(item,legacy_context=None):
 need(type(item) is dict and set(item)=={'review'},'Existing review ref entry required')
 review=read_ref(item['review'])
 need(set(review)==KEYS,'Existing v3 top-level closed fields required')
 refs={k:review[k] for k in KEYS if type(review[k]) is dict and k!='original_process'}
 need(set(refs)==KEYS-{'schema','status','source_head','root_screen_task','original_process'},'All actual v3 ref3 fields required')
 data={k:read_ref(v) for k,v in refs.items()}
 result=verify_decoded_review(review,data)
 return {'review':item['review'],**refs,**result}
def author_values(inputs):
 need(type(inputs) is dict and set(inputs)==INPUTS,'Exact author input fields required; future NULL rejected')
 for row in inputs.values():read_ref(row)
 deps=dependencies();guard=load_guard();values,pins=guard.fixed();facts=guard.keeper_closed(values)
 helpers={'results':facts['helpers_closed_value']['results'],'original_capture':deps['original_capture'],'retained_holder_final':facts['retained_holder_final'],
  'original_process_results':{'holder':{'session_id':47805,'pid':14760,'create_time':1791316356.256702,'result':inputs['original_holder_process_result']},
  'keeper':{'session_id':65664,'pid':19880,'create_time':1791313373.0698714,'result':inputs['original_keeper_process_result']}}}
 native=read_ref(inputs['original_native_observation']);ft=native['result']['process_observation']['creation_filetime_100ns']
 review={'schema':'lyd.root.previous-cold-boundary-review.v3','status':'ROOT_REVIEWED_ACTUAL_CLOSED_RELEASED_BOUNDARY','source_head':HEAD,'root_screen_task':TASK,
  'original_process':{'pid':14452,'process_create_time':1791313780.8972144,'process_creation_filetime_100ns':ft},
  'launch':deps['launch'],'original_handle_observation':inputs['original_handle_observation'],'original_native_observation':inputs['original_native_observation'],
  'helpers_closed':None,'process_absence':inputs['process_absence'],'keeper_final':facts['keeper_final'],'release_receipt':inputs['release_receipt'],'after_list':inputs['after_list'],
  'consumer_closed':facts['consumer_closed'],'consumer_session':deps['consumer_session'],'consumer_close_result':facts['consumer_close_result']}
 data={k:read_ref(v) for k,v in review.items() if type(v) is dict and k!='original_process'};data['helpers_closed']=helpers
 checked=verify_decoded_review(review,data)
 return review,helpers,checked
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--review',required=True,type=Path);p.add_argument('--sha256',required=True);a=p.parse_args()
 raw,row=byte_ref(a.review);need(row['sha256']==a.sha256.lower(),'Explicit actual review SHA differs')
 print(json.dumps(verify_previous_boundary_v3({'review':row}),ensure_ascii=False,indent=2))
if __name__=='__main__':main()

