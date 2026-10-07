"""ROOT-only one explicit spec -> exact author -> enqueue once -> bounded file poll.

No automatic attach/retry/reconnect, SDK calls from this process, game/proc/bus
operations, or gameplay policy. The already running official Client owns SDK
dispatch. --help never reads runtime inputs or creates files.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,re,subprocess,sys,time,traceback
sys.dont_write_bytecode=True
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004').resolve()
ATTACH='ck3_attach_profile_bridge_v1'
PROFILE_KEYS={'schema_version','guard_profile','guard_profile_sha256','userdir','state_directory','evidence_directory','game_version','dll','injector','normal_exit_source_inventory'}
def need(ok,message):
 if not ok:raise ValueError(message)
def ref(path):
 p=Path(path).resolve();raw=p.read_bytes();return {'path':p.as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def pin(path,sha):
 p=Path(path).resolve();row=ref(p);need(row['sha256']==sha.lower(),'Explicit actual SHA differs: '+str(p));return p,row
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def put(path,value):
 with Path(path).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
def same(a,b):return Path(a).resolve()==Path(b).resolve()
def short_matches(row,path,sha):return type(row) is dict and set(row)=={'path','sha256'} and same(row['path'],path) and row['sha256'].lower()==sha.lower()
def frozen_inputs(a):
 run=a.run_directory.resolve();need(run==BASE/'live-attempt-017','Only actual allocated R17 run admitted')
 need(re.fullmatch('[0-9a-f]{40}',a.expected_head) is not None,'Actual clean HEAD required')
 source=a.consumer_source.resolve();index_path,index_ref=pin(source/'INDEX.json',a.consumer_index_sha256);index=read(index_path)
 need(index['status']=='ACTUAL_GRANT28_METADATA_BOUND_R17_FORMAL_CONSUMER_SOURCE_ONLY' and index['attempt_id']=='R0017' and index['source_revision']==a.expected_head and same(index['run_root'],run),'Actual current R17 formal consumer source required')
 rows={Path(row['path']).resolve():row for row in index['files']}
 queue_helper=source/'persistent_native_mcp_queue_28.py';queue_ref=ref(queue_helper);need(rows.get(queue_helper)==queue_ref,'Actual frozen queue helper differs')
 author,author_ref=pin(a.request_author,a.request_author_sha256);need(author.name=='author_formal_request.py' and author.is_relative_to(BASE),'Exact external formal request author required')
 spec_path,spec_ref=pin(a.spec,a.spec_sha256);spec=read(spec_path);operation=spec.get('operation');required={'request_id','operation'}|({'name','arguments'} if operation=='call_tool' else set())
 need(operation in {'list_tools','call_tool','close'} and set(spec)==required,'Explicit closed root spec required')
 need(type(spec['request_id']) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,95}',spec['request_id']),'Fresh portable request ID required')
 if operation=='call_tool':need(type(spec['name']) is str and type(spec['arguments']) is dict,'Explicit tool and arguments object required')
 binding_path,binding_ref=pin(a.binding,a.binding_sha256);binding=read(binding_path)
 profile_path,profile_ref=pin(a.profile,a.profile_sha256);profile=read(profile_path)
 need(set(profile)==PROFILE_KEYS and profile['schema_version']==1 and profile['game_version']=='1.20.0.3','Read back current actual ten-field profile including normal exit inventory')
 need(binding['schema']=='ck3-root-official-mcp-consumer-binding-v1' and binding['source_revision']==a.expected_head and binding['epoch_id']==a.epoch_id and binding['attempt_id']=='R0017' and same(binding['run_root'],run),'Actual current ROOT binding source/run/epoch required')
 need(short_matches(binding['profile'],profile_path,profile_ref['sha256']),'Current actual profile must be exact ROOT-bound profile')
 queue=a.queue_directory.resolve();client=a.client_output.resolve()
 need(queue.is_relative_to(run) and client.is_relative_to(run) and queue!=client and same(binding['queue_directory'],queue) and same(binding['client_output_directory'],client),'Actual same-run queue/client paths required')
 for key,relative in [('userdir','userdir'),('state_directory','native-state'),('evidence_directory','native-evidence')]:need(same(profile[key],run/relative),'Current profile isolated path differs')
 normal=profile['normal_exit_source_inventory'];need(type(normal) is dict and set(normal)=={'path','sha256'} and same(normal['path'],run/'userdir/normal-exit-source-inventory-v1.json') and normal==binding['normal_exit_source_inventory'],'Known tenth-field normal exit inventory differs');pin(normal['path'],normal['sha256'])
 guard_path,guard_ref=pin(profile['guard_profile'],profile['guard_profile_sha256']);guard=read(guard_path)
 need(short_matches(binding['guard'],guard_path,guard_ref['sha256']) and all(guard['target'][key]==binding['target'][key] for key in ['pid','process_create_time']),'Original target identity/guard differs')
 session_path=client/'session.json';session_ref=ref(session_path);session=read(session_path);ready_ref=ref(client/'ready.json');ready=read(ready_ref['path'])
 need(session['client_session_id']==ready['client_session_id']==a.client_session_id and session['epoch_id']==ready['epoch_id']==a.epoch_id and session['source_revision']==a.expected_head and session['target']==binding['target'],'Actual current Client session/epoch/source/identity required')
 need(same(session['profile'],profile_path) and session['profile_sha256']==profile_ref['sha256'] and same(session['binding_file'],binding_path) and session['binding_sha256']==binding_ref['sha256'] and same(session['queue'],queue),'Original Client must use this actual profile/binding/queue')
 need(not (client/'session-closed.json').exists() and not (client/'session-terminated.json').exists(),'Client already closed/terminated; no reopen or replay')
 native_ref=None
 if a.phase=='pre-attach':
  need(operation=='list_tools' or (operation=='call_tool' and spec['name']==ATTACH),'Pre-attach phase only allows explicit list_tools or attach once')
  need(a.native_session_id is None and a.attach_native is None and a.attach_native_sha256 is None,'Native facts remain absent before actual attach')
 else:
  need(a.native_session_id is not None and a.attach_native is not None and a.attach_native_sha256 is not None,'Actual original native attach descriptor required for attached phase')
  native_path,native_ref=pin(a.attach_native,a.attach_native_sha256);need(native_path.is_relative_to(client) and '.native-' in native_path.name,'Use official Client-preserved native attach copy')
  native=read(native_path);need(native['schema']=='ck3.native-profile-receipt.v1' and native['status']=='attached_snapshot_verified' and native['session_id']==a.native_session_id and native['profile_sha256']==profile_ref['sha256'],'Actual native attach/session/profile binding required')
  need(native['observation_after']['pid']==binding['target']['pid'] and native['observation_after']['process_create_time']==binding['target']['process_create_time'],'Original native attach host game identity differs')
  need(not (operation=='call_tool' and spec['name']==ATTACH),'Attached phase cannot replay attach')
 need(not (queue/(spec['request_id']+'.request.json')).exists() and not list(client.glob('*-'+spec['request_id']+'.request.json')) and not list(client.glob('*-'+spec['request_id']+'.response.json')),'Request ID already exists; never replay')
 return spec,{'spec':spec_ref,'consumer_index':index_ref,'request_author':author_ref,'queue_helper':queue_ref,'binding':binding_ref,'profile':profile_ref,'guard':guard_ref,'normal_exit_source_inventory':normal,'Client_session':session_ref,'Client_ready':ready_ref,'original_native_attach':native_ref}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for key in ['spec','request-author','binding','profile']:
  p.add_argument('--'+key,type=Path,required=True);p.add_argument('--'+key+'-sha256',required=True)
 p.add_argument('--consumer-source',type=Path,required=True);p.add_argument('--consumer-index-sha256',required=True)
 for key in ['run-directory','queue-directory','client-output','output']:p.add_argument('--'+key,type=Path,required=True)
 for key in ['expected-head','epoch-id','client-session-id']:p.add_argument('--'+key,required=True)
 p.add_argument('--phase',choices=['pre-attach','attached'],required=True)
 p.add_argument('--native-session-id');p.add_argument('--attach-native',type=Path);p.add_argument('--attach-native-sha256')
 p.add_argument('--wait-seconds',type=float,default=60);a=p.parse_args();out=None;calls=[];enqueued=False;inputs=None
 try:
  need(0<=a.wait_seconds<=60,'Poll deadline must remain within 0..60 seconds')
  spec,inputs=frozen_inputs(a);out=a.output.resolve();need(out.is_relative_to(a.run_directory.resolve()) and not out.exists(),'Fresh same-run request execution output required');out.mkdir(parents=True,exist_ok=False)
  with (out/'SPEC.original.json').open('xb') as f:f.write(a.spec.read_bytes())
  argv=[sys.executable,'-B','-X','utf8',str(a.request_author.resolve()),'--consumer-source',str(a.consumer_source.resolve()),'--consumer-index-sha256',a.consumer_index_sha256,'--operation',spec['operation'],'--request-id',spec['request_id'],'--output',str(out/'REQUEST.actual.json')]
  if spec['operation']=='call_tool':put(out/'ARGUMENTS.actual.json',spec['arguments']);argv.extend(['--tool',spec['name'],'--arguments',str(out/'ARGUMENTS.actual.json')])
  for name,command in [('author',argv),('enqueue',[sys.executable,'-B','-X','utf8',inputs['queue_helper']['path'],'enqueue','--queue',str(a.queue_directory.resolve()),'--request',str(out/'REQUEST.actual.json')])]:
   put(out/(name.upper()+'-ARGV.json'),{'argv':command,'cwd':'C:/workspace/ck3_eternal_recurrence','source_inputs':inputs})
   with (out/(name+'.stdout')).open('xb') as stdout,(out/(name+'.stderr')).open('xb') as stderr:completed=subprocess.run(command,cwd='C:/workspace/ck3_eternal_recurrence',stdout=stdout,stderr=stderr)
   row={'stage':name,'actual_exit_code':completed.returncode,'stdout':ref(out/(name+'.stdout')),'stderr':ref(out/(name+'.stderr'))};calls.append(row)
   if name=='enqueue':enqueued=completed.returncode==0
   need(completed.returncode==0,name+' failed; raw stdio retained; no retry')
  deadline=time.monotonic()+a.wait_seconds;responses=[]
  while True:
   responses=list(a.client_output.resolve().glob('*-'+spec['request_id']+'.response.json'))
   if responses or time.monotonic()>=deadline:break
   time.sleep(min(.2,max(0,deadline-time.monotonic())))
  need(len(responses)==1,'Exactly one response not available by bounded deadline; request may still complete; never re-enqueue')
  response_path=responses[0];response=read(response_path);response_ref=ref(response_path)
  need(response['request_id']==spec['request_id'] and response['request_sha256']==ref(out/'REQUEST.actual.json')['sha256'],'Actual response request binding differs')
  sdk_ref=None;is_error=None;native_copies=[]
  if 'sdk_result' in response:
   sdk_path=a.client_output.resolve()/response['sdk_result'];sdk_ref=ref(sdk_path);need(sdk_ref['sha256']==response['sdk_result_sha256'],'Actual SDK result bytes differ');sdk=read(sdk_path);is_error=sdk.get('isError')
   for native in response.get('native_receipts',[]):
    if 'copy' in native:
     copy_ref=ref(a.client_output.resolve()/native['copy']);need(copy_ref['sha256']==native['sha256'],'Official native copy changed');native_copies.append(copy_ref)
  transport_recorded=response['status'] in {'MCP_RESULT_RECORDED','CLIENT_CLOSE_REQUESTED'} and is_error is not True and response.get('is_error') is not True
  result={'status':'EXPLICIT_REQUEST_RECORDED' if transport_recorded else 'EXPLICIT_REQUEST_RED_PRESERVED','request_id':spec['request_id'],'inputs':inputs,'calls':calls,'request':ref(out/'REQUEST.actual.json'),'response':response_ref,'response_status':response['status'],'sdk_result':sdk_ref,'sdk_isError':is_error,'official_native_copies':native_copies,'automatic_retry':False,'automatic_attach':False,'automatic_reconnect':False,'enqueued_once':True,'formal_acceptance':None,'new_T':None,'finished_at_utc':datetime.now(timezone.utc).isoformat()}
  put(out/'RESULT.actual.json',result);print(json.dumps({'result':ref(out/'RESULT.actual.json'),'response':response,'formal_acceptance':None},ensure_ascii=False));return 0 if transport_recorded else 1
 except Exception as error:
  result={'status':'EXPLICIT_REQUEST_RED_NO_RETRY','error':str(error),'error_type':type(error).__name__,'traceback':traceback.format_exc(),'inputs':inputs,'calls':calls,'enqueue_exit0_observed':enqueued,'may_complete_later':enqueued,'replay_authorized':False,'formal_acceptance':None,'finished_at_utc':datetime.now(timezone.utc).isoformat()}
  if out is not None and out.exists() and not (out/'RESULT.actual.json').exists():put(out/'RESULT.actual.json',result)
  print(json.dumps(result,ensure_ascii=False));return 1
if __name__=='__main__':raise SystemExit(main())
