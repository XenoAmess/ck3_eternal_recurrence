"""Pure A04 owner projection: retain worker; original Task checks its Job tail."""
import hashlib

BASE_SHA = '50b834f7a7ea16654f8bd673f3ae425eeb8a27fb1ca4d9714679770670d81d56'

RUNTIME = '''def _wait_recording_worker_v1(worker):
    import ctypes as C
    k=worker.kernel
    while True:
        state=k.WaitForSingleObject(worker.handle,100)
        if state==0:break
        if state!=258:raise RuntimeError('retained recording worker wait failed')
    k.GetExitCodeProcess.argtypes=[C.c_void_p,C.POINTER(C.c_ulong)]
    k.GetExitCodeProcess.restype=C.c_int
    code=C.c_ulong()
    if not k.GetExitCodeProcess(worker.handle,C.byref(code)):
        raise C.WinError(C.get_last_error())
    return {'worker_exit_code':code.value,'job_tail':'JOB_TAIL_PENDING_ORIGINAL_OWNER',
            'job_tail_check_scope':'original Task retained Job after this stage exits'}


def _recording_worker_terminal_v1(worker,request,capture,game_pid,game_birth):
    import hashlib,re
    result=_wait_recording_worker_v1(worker)
    root=Path(request['receipt_root']).resolve()
    sid=request['session_id']
    require(root.name==sid,'retained worker session differs')
    result.update(schema='xar.recording-owner-worker-closed/v1',machine_id=SPEC['machine_id'],
        session_id=sid,worker_pid=request['worker_pid'],
        worker_creation_filetime=request['worker_creation_filetime'],
        forced_process_calls=0,video_body_bytes_read=0)
    failure=root/'media-finalization-failed.json'
    complete=root/'completed.json'
    if result['worker_exit_code']!=0:
        result['status']='WORKER_EXIT_NONZERO'
    elif failure.exists():
        result['status']='MEDIA_FINALIZATION_FAILED'
    elif not complete.exists():
        result['status']='MEDIA_TERMINAL_MISSING'
    else:
        validated=capture.read_capture_closed_receipt(root,session_id=sid,game_pid=game_pid,
            game_creation_filetime=game_birth,recording_worker_pid=request['worker_pid'],
            recording_root=root.parent)
        raw=complete.read_bytes()
        require(len(raw)<=1048576,'finite final media receipt required')
        value=json.loads(raw)
        closed=read(root/'capture_closed.json')
        require(validated is not None and value.get('state')=='completed'
            and value.get('path')==closed['output_path']
            and value.get('bytes')==closed['output_bytes']
            and isinstance(value.get('sha256'),str)
            and re.fullmatch('[a-f0-9]{64}',value['sha256']) is not None,
            'actual final media receipt differs')
        result.update(status='WORKER_MEDIA_NORMAL_CLOSED_JOB_TAIL_PENDING',
            completed={'path':str(complete),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    if failure.exists():result['media_failure_path']=str(failure)
    return result


'''

OLD_FINALLY = '''    finally:
        # The original owner keeps its child handle. Runtime requests STOP only
        # after OBS normal exit/unbound; no capture error silently kills it.
        if owner.process is not None:
            owner.process.wait()
            print(json.dumps({'publisher_normal_closed':owner.close()}),flush=True)
'''
NEW_FINALLY = '''    finally:
        try:
            # Original publisher close ordering remains unchanged.
            if owner.process is not None:
                owner.process.wait()
                print(json.dumps({'publisher_normal_closed':owner.close()}),flush=True)
        finally:
            if retained_recording_worker is not None:
                try:
                    proof=_recording_worker_terminal_v1(retained_recording_worker,
                        request,capture,a.game_pid,a.game_birth)
                    api.atomic(N/('ROOT-RECORDING-WORKER-CLOSED-'+SPEC['generation']+'.json'),proof,new=True)
                    require(proof['status']=='WORKER_MEDIA_NORMAL_CLOSED_JOB_TAIL_PENDING',
                        'recording worker finalization failed: '+proof['status'])
                finally:retained_recording_worker.close()
'''


def project(raw):
    if len(raw)!=11359 or hashlib.sha256(raw).hexdigest()!=BASE_SHA:
        raise ValueError('exact A04 routed original owner required')
    patches=[('def main():',RUNTIME+'def main():'),
        ('    owner=api.PublisherOwner(config_path)\n    try:',
         '    owner=api.PublisherOwner(config_path)\n    retained_recording_worker=None\n    try:'),
        ("        request.update(capture_admission_stage='saved_map'",
         "        Generation,*_=capture._generation_helpers()\n"
         "        retained_recording_worker=Generation(request['worker_pid'],\n"
         "            Path(request['worker_executable']),creation_filetime=request['worker_creation_filetime'])\n"
         "        request.update(capture_admission_stage='saved_map'"),
        (OLD_FINALLY,NEW_FINALLY)]
    text=raw.decode('utf-8')
    for before,after in patches:
        if text.count(before)!=1:raise ValueError('exact retained owner seam differs')
        text=text.replace(before,after,1)
    result=text.encode()
    compile(result,'A04-retained-recording-worker-owner','exec')
    for before,after in reversed(patches):
        if text.count(after)!=1:raise ValueError('inverse owner seam differs')
        text=text.replace(after,before,1)
    if text.encode()!=raw:raise ValueError('owner changed outside retained-worker hunks')
    return result
