"""R14 actual receipts only: original HANDLE exit0, normal Client close and CAS release."""
from pathlib import Path
from datetime import datetime
import hashlib,json,importlib.util,sys
HERE=Path(__file__).resolve().parent
def need(ok,message):
    if not ok:raise ValueError(message)
def read_ref(row):
    need(type(row) is dict and set(row)=={'path','bytes','sha256'},'Exact actual boundary ref3 required')
    p=Path(row['path']);need(p.is_absolute(),'Absolute boundary ref required')
    for q in (p,*p.parents):need(not q.is_symlink() and not q.is_junction(),'Linked boundary input refused')
    raw=p.read_bytes();need(len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],'Actual R14 boundary bytes/SHA changed')
    return json.loads(raw)
def same(a,b):return Path(a).resolve()==Path(b).resolve()
def stamp(value):
    d=datetime.fromisoformat(value.replace('Z','+00:00'));need(d.tzinfo is not None,'Actual aware boundary timestamp required');return d
def validate_original_exit_result(result):
    schema=result.get('schema')
    need(schema in ('ck3-normal-exit-process-observation-result-v1','ck3-normal-exit-request-result-v1'),'Actual normal-exit request or retained-process observation schema required')
    pins=json.loads((HERE/'DEPENDENCIES.json').read_bytes());row=pins['normal_exit_contract'];observer=pins['normal_exit_process_observer']
    for stamp in (row,observer):
        path=Path(stamp['path']);raw=path.read_bytes();need(len(raw)==stamp['bytes'] and hashlib.sha256(raw).hexdigest()==stamp['sha256'],'Actual source normal-exit typed validator changed')
    path=Path(row['path']);sys.path.insert(0,str(path.parent));spec=importlib.util.spec_from_file_location('r15_normal_exit_typed_contract',path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    if schema=='ck3-normal-exit-request-result-v1':
        module.normalize_public_exit_result(result,action='confirm_desktop',expected_revision=result['public_revision'])
        need(result.get('native_submission_count')==1 and type(result.get('native_submission_count')) is int,'Direct actual confirm must retain its one native submission')
    else:module.normalize_public_exit_observation_result(result)
    return result

def verify_previous_boundary_v3(item,legacy_context=None):
    need(type(item) is dict and set(item)=={'review'},'Actual previous-boundary review ref required')
    review=read_ref(item['review'])
    keys={'schema','status','source_head','root_screen_task','original_process','launch','original_handle_observation','original_native_observation','helpers_closed','process_absence','keeper_final','release_receipt','after_list','consumer_closed','consumer_session','consumer_close_result'}
    need(set(review)==keys and review['schema']=='lyd.root.previous-cold-boundary-review.v3' and review['status']=='ROOT_REVIEWED_ACTUAL_CLOSED_RELEASED_BOUNDARY','Original boundary review fields/status differ')
    need(review['source_head']=='19e660105e05395caa6cc95e76c299312ee89d51','Future R14 closure must bind genuine HEAD19')
    need(same(review['launch']['path'],'C:/workspace/ck3_lyd_runtime_20261004/live-attempt-014/launch.json'),'Future R14 original launch required, not R13 closure')
    refs={k:review[k] for k in keys if type(review[k]) is dict and k!='original_process'}
    data={k:read_ref(v) for k,v in refs.items()}
    process=review['original_process'];launch=data['launch'];session=data['consumer_session']
    need(launch['game_started'] is True and launch['status']=='GAME_CREATED_REQUIRES_NATIVE_LOAD_READBACK' and launch['source_revision']==review['source_head'] and launch['pid']==process['pid'] and launch['process_create_time']==process['process_create_time'],'Original R14 launch/process differs')
    sdk=data['original_handle_observation'];native=data['original_native_observation']
    need(sdk.get('isError') is False and sdk.get('resultType')=='complete' and sdk.get('structuredContent')==native and sdk.get('content') and json.loads(sdk['content'][0]['text'])==native,'Original game SDK/native/text receipts disagree')
    result=validate_original_exit_result(native['result']);observed=result['process_observation'];before=result['process_preconfirm_pin']
    need(native['schema']=='ck3.native-profile-receipt.v1' and native['status']==result['status']=='process_exit_observed_zero' and result['schema'] in ('ck3-normal-exit-process-observation-result-v1','ck3-normal-exit-request-result-v1') and result['action']=='confirm_desktop','Actual typed normal game exit result required')
    for row in (before,observed):need(row['pid']==process['pid'] and row['creation_filetime_100ns']==process['process_creation_filetime_100ns'],'Original game HANDLE identity differs')
    need(type(before['retained_handle_token']) is str and bool(before['retained_handle_token']) and observed['retained_handle_token']==before['retained_handle_token'] and before['wait_result']==258 and observed['wait_result']==0 and observed['wait_state']=='signaled' and observed['exit_code']==0 and observed['process_identity_verified'] is True and observed['process_exit_observed'] is True and observed['errors']==[],'Original retained game HANDLE exit0 missing')
    need(result['process_exit_observed'] is True and result['exit_code']==0 and result['typed_normal_exit_observed'] is True and result['autosave_verified'] is False and result['claim_consumed'] is True and result['retry_authorized'] is False,'Typed game exit closure differs; autosave cannot be credited')
    need(native['profile_sha256']==session['profile_sha256'] and session['target']=={'pid':process['pid'],'process_create_time':process['process_create_time']} and session['source_revision']==review['source_head'] and session['automatic_attach'] is False and session['automatic_retry'] is False and session['cache'] is None,'Original Client profile/source/target differs')
    profile=read_ref({'path':session['profile'],'bytes':Path(session['profile']).stat().st_size,'sha256':session['profile_sha256']})
    guard=read_ref({'path':profile['guard_profile'],'bytes':Path(profile['guard_profile']).stat().st_size,'sha256':profile['guard_profile_sha256']})
    need(guard['target']['pid']==process['pid'] and guard['target']['process_create_time']==process['process_create_time'] and guard['screen_task_id']==review['root_screen_task'],'Original Client guard differs')
    closed=data['consumer_closed'];response=data['consumer_close_result']
    need(closed['attach_requested'] is True and not (Path(refs['consumer_closed']['path']).parent/'session-terminated.json').exists(),'Normal Client completion missing')
    request=read_ref({'path':response['request_path'],'bytes':Path(response['request_path']).stat().st_size,'sha256':response['request_sha256']})
    need(response['status']=='CLIENT_CLOSE_REQUESTED' and request['operation']=='close' and request['request_id']==response['request_id'] and Path(response['request_path']).name in closed['claimed_requests'] and same(str(Path(response['request_path']).parent),session['queue']),'Actual terminal claimed Client close differs')
    need(stamp(session['started_at_utc'])<=stamp(response['started_at_utc'])<=stamp(response['finished_at_utc'])<=stamp(closed['closed_at_utc']),'Actual Client close time ordering differs')
    rows=data['helpers_closed']['results'];need(len(rows)==2 and {r['role'] for r in rows}=={'client','keeper'},'Actual original Client and keeper HANDLE closure required')
    roles={r['role']:r for r in rows}
    for role,row in roles.items():
        need(row['handle_retained_before_close'] is True and row['wait_result']==0 and row['exit_code']==0 and type(row['create_time']) in (int,float),'Original helper retained HANDLE exit0 missing')
        start=read_ref(row['source'])
        need(row['pid']==start.get('pid',start.get('PID')) and row['cmdline']==start['argv'],'Original helper start/closure command differs')
        need(stamp(row['observed_at_utc'])>=stamp(closed['closed_at_utc']),'Helper closure precedes Client terminal close')
    need(session['profile'] in roles['client']['cmdline'] or any(same(v,session['profile']) for v in roles['client']['cmdline'] if ':' in v),'Closed original Client profile differs')
    final=data['keeper_final'];need(final['task_id']==review['root_screen_task'] and final['failure'] is None and final['entry_error'] is None and final['thread_exited'] is True and final['screen_released'] is False and final['game_actions'] is False,'Keeper FINAL closure missing or failed')
    release=data['release_receipt'];need(release['schema']=='codex.task_bus.v1' and release['ok'] is True and release['task']['task_id']==release['event']['task_id']==review['root_screen_task'] and release['task']['resources']==release['event']['resources']==[] and release['task']['state']=='done' and release['task']['last_sequence']==release['event']['sequence'] and release['event']['sequence']>final['last_sequence'],'Actual R14 CAS screen release missing')
    listed=data['after_list'];need(listed['schema']=='codex.task_bus.v1' and listed['ok'] is True and type(listed['tasks']) is list and not any('ck3-screen:acquired' in r['resources'] for r in listed['tasks']),'Actual after-release sole-screen vacancy missing')
    absent=data['process_absence'];need(absent['same_original_identities_absent'] is True and absent['no_current_managed_game_or_native_services'] is True and absent['remaining_managed_game_or_native_services']==[] and all(r['same_original_identity_alive'] is False for r in absent['original_identities']),'Actual original processes/services absence missing')
    need(stamp(absent['observed_at_utc'])>=stamp(release['event']['timestamp_utc']),'Process absence predates release')
    return {'review':item['review'],**refs,'actual_prior_identity':process,'actual_prior_source_head':review['source_head'],'actual_prior_task':review['root_screen_task'],
            'actual_exit_observation_limits':{'game_original_HANDLE_exit0_observed':True,'client_exit_code':roles['client']['exit_code'],'keeper_exit_code':roles['keeper']['exit_code'],'client_OS_exit0_observed':True,'keeper_OS_exit0_observed':True,'native_session_id':native['session_id'],'consumer_session_id':session['client_session_id'],'autosave_verified':False}}

def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review',required=True,type=Path);parser.add_argument('--sha256',required=True)
    args=parser.parse_args();raw=args.review.read_bytes()
    need(hashlib.sha256(raw).hexdigest()==args.sha256,'Explicit actual R14 boundary SHA changed')
    row={'path':args.review.resolve().as_posix(),'bytes':len(raw),'sha256':args.sha256}
    result=verify_previous_boundary_v3({'review':row})
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
