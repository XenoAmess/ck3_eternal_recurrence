"""One bounded original-request review responder. The current executor supplies the decision after inspection."""
from pathlib import Path
import ctypes,datetime,hashlib,json,os,re,subprocess,sys,time
from ctypes import wintypes

def require(condition,message='diagnostic contract condition failed'):
    if not condition:raise ValueError(message)


def pairs(items):
    result={}
    for key,value in items:
        if key in result:raise ValueError('duplicate JSON member')
        result[key]=value
    return result
def parse(raw):return json.loads(raw,object_pairs_hook=pairs)
def utc(text):
    value=datetime.datetime.fromisoformat(text.replace('Z','+00:00'))
    require((value.utcoffset()==datetime.timedelta(0)), 'UTC required')
    return value
def now():return datetime.datetime.now(datetime.timezone.utc)
def stamp():return now().isoformat()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def write_once(path,value):
    with path.open('x',encoding='utf-8',newline=chr(10)) as stream:json.dump(value,stream,indent=2);stream.write(chr(10))
def exact(reference,limit,root=None):
    require((set(reference)=={'path','bytes','sha256'}), 'diagnostic contract condition failed')
    path=Path(reference['path']).absolute();require((path.resolve()==path and path.is_file() and not path.is_symlink()), 'diagnostic contract condition failed')
    if root is not None:require((path.is_relative_to(root)), 'diagnostic contract condition failed')
    require((type(reference['bytes']) is int and 0<reference['bytes']<=limit), 'diagnostic contract condition failed')
    require((re.fullmatch('[0-9a-f]{64}',reference['sha256'])), 'diagnostic contract condition failed')
    raw=path.read_bytes();require((len(raw)==reference['bytes'] and sha(raw)==reference['sha256']), 'diagnostic contract condition failed');return raw
def own_birth():
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetCurrentProcess.restype=wintypes.HANDLE
    kernel.GetProcessTimes.argtypes=[wintypes.HANDLE,*([ctypes.POINTER(wintypes.FILETIME)]*4)]
    kernel.GetProcessTimes.restype=wintypes.BOOL
    creation,exit_time,kernel_time,user_time=[wintypes.FILETIME() for unused in range(4)]
    if not kernel.GetProcessTimes(kernel.GetCurrentProcess(),ctypes.byref(creation),ctypes.byref(exit_time),ctypes.byref(kernel_time),ctypes.byref(user_time)):
        raise ctypes.WinError(ctypes.get_last_error())
    return str((creation.dwHighDateTime<<32)|creation.dwLowDateTime)

require((len(sys.argv)==3), 'CONFIG exactSHA required')
config_path=Path(sys.argv[1]).resolve();raw=config_path.read_bytes();require((sha(raw)==sys.argv[2]), 'diagnostic contract condition failed')
C=parse(raw)
require((set(C)=={'schema','queue_root','material_root','output_root','prefix','main_begin','main_end','own_stop',
                'stop_before_utc','source_expires_at_utc','expected_machine_id','expected_session_id','expected_game'}), 'diagnostic contract condition failed')
require((C['schema']=='ck3.single-original-review-watch/v1'), 'diagnostic contract condition failed')
queue,materials,output=[Path(C[key]).absolute() for key in ('queue_root','material_root','output_root')]
require((all(path.resolve()==path for path in (queue,materials,output))), 'diagnostic contract condition failed')
require((not any(a.is_relative_to(b) for a,b in ((output,queue),(output,materials),(queue,materials),(materials,queue)))), 'diagnostic contract condition failed')
prefix=Path(C['prefix']['path']).absolute();exact(C['prefix'],131072)
begin_file,end_file,own_stop=[Path(C[key]).absolute() for key in ('main_begin','main_end','own_stop')]
stop=min(utc(C['stop_before_utc']),utc(C['source_expires_at_utc']))
remaining=(stop-now()).total_seconds();require((0<remaining<=2700), 'finite original source stop required')
source_monotonic_end=time.monotonic()+remaining
require((set(C['expected_game'])=={'pid','creation_filetime'}), 'diagnostic contract condition failed')
require((type(C['expected_game']['pid']) is int and C['expected_game']['pid']>0), 'diagnostic contract condition failed')
require((C['expected_machine_id'] and C['expected_session_id']), 'diagnostic contract condition failed')
output.mkdir(parents=True,exist_ok=True)
for leaf in ('tmp-own','jna-own'):(output/leaf).mkdir(exist_ok=True)
lock=output/'SINGLE-FIRST-RESPONDER.lock'
lock_handle=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
os.write(lock_handle,json.dumps({'pid':os.getpid(),'creation_filetime':own_birth(),'config_sha256':sha(raw)}).encode('utf-8'))
ready={'schema':'ck3.single-original-review-watcher-running/v1','at_utc':stamp(),'pid':os.getpid(),'creation_filetime':own_birth(),
       'config':{'path':str(config_path),'bytes':len(raw),'sha256':sha(raw)},'prefix':C['prefix'],
       'script_sha256':sha(Path(__file__).read_bytes()),'stop_before_utc':C['stop_before_utc'],
       'source_expires_at_utc':C['source_expires_at_utc'],'actually_running_before_Main':not begin_file.exists(),
       'only_one_response':True,'automatic_decision':False,'no_Game_pipe_HTTP_writer_API':True}
require((ready['actually_running_before_Main']), 'watcher must actually begin before Main')
write_once(output/'WATCHER.READY.json',ready);print(json.dumps(ready),flush=True)
outcome=None
def finish(status,**details):
    global outcome
    outcome={'schema':'ck3.single-original-review-watcher-result/v1','at_utc':stamp(),'status':status,'pid':os.getpid(),**details}
    write_once(output/'WATCHER.END.json',outcome);print(json.dumps(outcome),flush=True)
def active():return not end_file.exists() and now()<stop and time.monotonic()<source_monotonic_end
def cli(stage,request,request_sha,deadline,monotonic_end,selection=None,inspection=None):
    exact(C['prefix'],131072)
    seconds=min((deadline-now()).total_seconds(),monotonic_end-time.monotonic(),source_monotonic_end-time.monotonic())
    require((active() and seconds>2), 'original earlier deadline or Main ended')
    argv=['C:/jdk-21/bin/java.exe','-XX:ActiveProcessorCount=1','-Xmx768m','--enable-native-access=ALL-UNNAMED',
          '-Djava.io.tmpdir='+str(output/'tmp-own'),'-Djna.tmpdir='+str(output/'jna-own'),
          '@'+str(prefix),stage,str(request),request_sha,str(materials)]
    if stage=='respond':argv.extend([str(selection),str(inspection)])
    write_once(output/(stage+'.BEGIN.json'),{'at_utc':stamp(),'argv':argv,'original_request_sha256':request_sha,'effective_original_deadline':deadline.isoformat()})
    env=os.environ.copy()
    for key in ('TMP','TEMP','TMPDIR'):env[key]=str(output/'tmp-own')
    started=time.monotonic()
    with (output/(stage+'.stdout')).open('xb') as stdout,(output/(stage+'.stderr')).open('xb') as stderr:
        child=subprocess.Popen(argv,cwd=output,env=env,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
        try:code=child.wait(timeout=min(25,seconds-1))
        except subprocess.TimeoutExpired:child.kill();child.wait();code=124
    write_once(output/(stage+'.END.json'),{'at_utc':stamp(),'exit':code,'seconds':time.monotonic()-started})
    require((code==0), stage+' failed; never retry or synthesize inspection')
    result=output/(stage+'.stdout');require((result.stat().st_size<=262144), 'diagnostic contract condition failed')
    return parse(result.read_bytes())
try:
    request=None
    while active():
        if begin_file.exists() and queue.is_dir():
            candidates=[]
            for path in queue.glob('*/ready.json'):
                require((not path.is_symlink() and path.resolve()==path.absolute()), 'diagnostic contract condition failed')
                if path.parent.joinpath('archived.json').exists() or path.parent.joinpath('expired.json').exists():continue
                require((path.stat().st_size<=16384), 'diagnostic contract condition failed')
                event=parse(path.read_bytes())
                if event.get('schema')=='xar.ordinary-codex-file-progress/v1' and event.get('status')=='ORDINARY_CODEX_REQUEST_READY':candidates.append((path,event))
            require((len(candidates)<=1), 'ambiguous first request; no response')
            if candidates:
                path,event=candidates[0];request=path.parent/'request.json'
                require((re.fullmatch('codex-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',path.parent.name)), 'diagnostic contract condition failed')
                require((request.resolve()==request.absolute() and request.is_relative_to(queue)), 'diagnostic contract condition failed')
                require((request.stat().st_size<=16384), 'diagnostic contract condition failed')
                request_raw=request.read_bytes();request_sha=sha(request_raw);row=parse(request_raw)
                require((request_sha==event['request_sha256'] and row['request_id']==event['request_id']==path.parent.name), 'diagnostic contract condition failed')
                require((Path(event['request_file']).resolve()==request and row['deadline_utc']==event['deadline_utc']), 'diagnostic contract condition failed')
                require((row['schema']=='xar.ordinary-codex-file-request/v2' and row['provider']=='codex-session'), 'diagnostic contract condition failed')
                require((row['machine_id']==C['expected_machine_id'] and row['before']['machine_id']==C['expected_machine_id']), 'diagnostic contract condition failed')
                require((row['before']['game']==C['expected_game']), 'diagnostic contract condition failed')
                require((Path(row['response_file']).resolve()==request.parent/'response.json'), 'diagnostic contract condition failed')
                require((not request.parent.joinpath('response.json').exists()), 'diagnostic contract condition failed')
                command_raw=exact(row['original_command'],1048576,materials);command=parse(command_raw)
                require((command['session_id']==C['expected_session_id'] and command['action_id']==row['proposal_id']), 'diagnostic contract condition failed')
                require((sha(command_raw)==row['body_sha256'] and command['before']==row['before']), 'diagnostic contract condition failed')
                created,original_deadline=utc(row['created_at_utc']),utc(row['deadline_utc'])
                require((0<(original_deadline-created).total_seconds()<=120), 'diagnostic contract condition failed')
                deadline=min(original_deadline,utc(command['deadline']),stop)
                seconds=(deadline-now()).total_seconds();require((2<seconds<=120), 'diagnostic contract condition failed')
                monotonic_end=time.monotonic()+seconds
                write_once(output/'ACTUAL-FIRST-READY.json',{'at_utc':stamp(),'request':str(request),'request_sha256':request_sha,
                           'original_file_deadline':row['deadline_utc'],'original_command_deadline':command['deadline'],
                           'earliest_deadline':deadline.isoformat(),'no_deadline_renewal':True})
                # SELECT must reach the real Controller before any operator stop. This watcher never writes stop.
                inspected=cli('inspect',request,request_sha,deadline,monotonic_end)
                require((inspected['schema']=='xar.ordinary-codex-session-inspection/v1'), 'inspection schema differs')
                require((inspected['request']['sha256']==request_sha and inspected['deadline_utc']==row['deadline_utc']), 'inspection original identity differs')
                def file_ref(path):
                    data=path.read_bytes()
                    return {'path':str(path),'bytes':len(data),'sha256':sha(data)}
                review={'schema':'ck3.single-original-codex-review-required/v1','at_utc':stamp(),'pid':os.getpid(),
                        'request':file_ref(request),'inspection':file_ref(output/'inspect.stdout'),
                        'payload':inspected['payload'],'original_command':inspected['original_command'],
                        'request_id':row['request_id'],'proposal_id':row['proposal_id'],'body_sha256':row['body_sha256'],
                        'before':row['before'],'original_file_deadline':row['deadline_utc'],
                        'original_command_deadline':command['deadline'],'earliest_deadline':deadline.isoformat(),
                        'selection_path':str(output/'selection.json'),'requires_current_executor_review':True,
                        'no_automatic_decision':True,'no_deadline_renewal':True}
                write_once(output/'REVIEW.READY.json',review);print(json.dumps(review),flush=True)
                selection=output/'selection.json'
                while active() and now()<deadline and time.monotonic()<monotonic_end and not selection.is_file():time.sleep(.02)
                if not selection.is_file():
                    finish('MAIN_ENDED_WITHOUT_SELECTION' if end_file.exists() else 'ORIGINAL_REQUEST_EXPIRED_WITHOUT_SELECTION')
                    break
                require(selection.resolve()==selection.absolute() and not selection.is_symlink() and selection.stat().st_size<=262144,'bounded own selection required')
                selected=parse(selection.read_bytes())
                require(set(selected)=={'decision','proposal_id','body_sha256','reason'},'exact original selection fields required')
                require(selected['decision'] in ['SELECT_PROPOSAL','WAIT'],'current executor must select or wait explicitly')
                require(selected['proposal_id']==row['proposal_id'] and selected['body_sha256']==row['body_sha256'],'selection crossed original proposal/body')
                require(type(selected['reason']) is str and 0<len(selected['reason'])<=32768,'bounded actual review reason required')
                selected['reason'].encode('utf-8',errors='strict')
                responded=cli('respond',request,request_sha,deadline,monotonic_end,selection,output/'inspect.stdout')
                require((responded['schema']=='xar.ordinary-codex-session-response-published/v1'), 'diagnostic contract condition failed')
                response=exact(responded['response'],262144)
                require((parse(response)['selection']==selected), 'response differs from the current executor selection')
                finish('ONE_ORIGINAL_REVIEW_RESPONSE_PUBLISHED',request=str(request),request_sha256=request_sha,response=responded['response'],
                       original_deadline_utc=row['deadline_utc'],source_deadline_unchanged=True)
                break
        time.sleep(.05)
    if outcome is None:finish('MAIN_ENDED_WITHOUT_RESPONSE' if end_file.exists() else 'ORIGINAL_SOURCE_WINDOW_ENDED_WITHOUT_RESPONSE')
except Exception as failure:
    if outcome is None:finish('FAILED_NO_RETRY',error=type(failure).__name__+': '+str(failure))
    raise
finally:os.close(lock_handle)
