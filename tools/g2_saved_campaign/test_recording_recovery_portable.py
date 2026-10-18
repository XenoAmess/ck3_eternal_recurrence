"""Focused offline adapter integration; no process, Game, MCP, OBS or desktop operations."""
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timezone
import ast,asyncio,copy,hashlib,json,sys,tempfile,time
import pytest
from PIL import Image,ImageDraw
import recording_recovery_adapter as m
from recording_recovery_supervisor import RecoverySupervisor

BASE=Path(__file__).resolve().parent
LIVE=BASE/'fixtures'
SOURCE=BASE/'recording_recovery_adapter.py'

class FakePlatform:
    def __init__(self,n,oldjob):
        self.n=n;self.oldjob=oldjob;self.launches=[];self.fail_launch=False;self.old_feeder_alive=False
        self.procs={501:(100501,True),502:(100502,False),503:(100503,False),
                    601:(100601,True),602:(100602,True)}
    def process(self,pid):
        row=self.procs.get(pid)
        return None if row is None else {'pid':pid,'creation_filetime':row[0],'alive':row[1],'exit_code':None if row[1] else 0}
    def alive(self,pid,stamp):
        row=self.process(pid)
        return bool(row and row['alive'] and row['creation_filetime']==stamp)
    def scripts(self,paths):
        return [{'pid':999,'creation_filetime':100999,'alive':True}] if self.old_feeder_alive else []
    def spawn(self,argv,stdout,stderr,*,cwd):
        self.launches.append(('overlay' if '--decision-text-file' in argv else 'feeder',list(argv)))
        Path(stdout).write_text('',encoding='utf-8');Path(stderr).write_text('',encoding='utf-8')
        pid=700+len(self.launches);stamp=100000+pid;self.procs[pid]=(stamp,True)
        if '--decision-text-file' in argv:
            text=Path(argv[argv.index('--decision-text-file')+1]);text.write_text('Actual test decision',encoding='utf-8')
            row={**self.oldjob['overlay'],'overlay_pid':pid,'overlay_creation_filetime':stamp,
                 'overlay_hwnd':pid+1000,'decision_text_file':str(text),'at_utc':m.utc().isoformat()}
            m.atomic(self.n/f'ROOT-DECISION-OVERLAY-{pid}-STARTED.json',row,new=True)
        return self.process(pid)
    def launch_recording(self,c,job,overlay_receipt):
        self.launches.append(('recording',str(overlay_receipt)))
        if self.fail_launch:raise OSError('unknown after launcher entered; no receipt')
        root=self.n/'recordings'/'new';root.mkdir()
        overlay=m.shared_json(overlay_receipt);stamp=m.utc().isoformat()
        new={**job,'session_id':'new','receipt_root':str(root),'overlay':overlay,
             'decision_text_file':overlay['decision_text_file']}
        m.atomic(root/'job.json',new,new=True)
        started={'state':'recording','at_utc':stamp,'game_pid':501,'game_creation_filetime':100501,
                 'capture_mode':'game_decision','decision_source':True,
                 'decision_settings':{'read_from_file':True,'file':overlay['decision_text_file']}}
        m.atomic(root/'started.json',started,new=True)
        self.procs[800]=(100800,True)
        m.atomic(root/'obs-launch.json',{'pid':800,'creation_filetime':100800},new=True)
        game=Image.new('RGB',(800,450),(80,130,160));scene=game.copy()
        ImageDraw.Draw(scene).rectangle((550,10,790,440),fill=(10,20,30))
        frame={'at_utc':m.utc().isoformat(),'mutable_latest_frame':True}
        for name,image in [('game',game),('scene',scene)]:
            p=root/f'recording-latest-{name}.png';image.save(p);data=p.read_bytes()
            frame[name]={'path':str(p),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
        m.atomic(root/'recording-latest.json',{'state':'recording','frame':frame},new=True)
        return {'session_id':'new','worker_pid':801,'receipt_root':str(root),'state':'requested'}

def fixture(base,*,mixed=False):
    n=base/'session';n.mkdir();(n/'recordings'/'old').mkdir(parents=True)
    for directory in ['p42-queue','p42-requests','p42-responses']:(n/directory).mkdir()
    launch={'pid':501,'creation_date':'test-game-time','pipe':'same-native-pipe'}
    launchpath=n/'launch.json';m.atomic(launchpath,launch,new=True)
    text=n/'old-decision.txt';text.write_text('Old decision',encoding='utf-8')
    stamp=m.utc().isoformat()
    overlay={'overlay_pid':502,'overlay_creation_filetime':100502,'overlay_hwnd':1502,
             'game_pid':501,'game_creation_filetime':100501,'game_hwnd':1000,
             'managed_desktop_id':'desktop-1','game_virtual_desktop':{'desktop_id':'desktop-1'},
             'overlay_virtual_desktop':{'desktop_id':'desktop-1'},'decision_text_file':str(text),
             'launch_receipt':str(launchpath),'at_utc':stamp}
    m.atomic(n/'ROOT-DECISION-OVERLAY-502-STARTED.json',overlay,new=True)
    admission=base/'STORAGE-ADMISSION.json';m.atomic(admission,{'status':'ADMITTED','approved_output_roots':[str(base)]},new=True)
    job={'session_id':'old','pid':501,'hwnd':1000,'game_creation_filetime':100501,'launch':launch,
         'receipt_root':str(n/'recordings'/'old'),'recording_root':str(n/'recordings'),
         'overlay':overlay,'capture_mode':'game_decision','continuous':True,
         'duration_seconds':None,'max_output_bytes':None,'deadline_utc':None,
         'decision_text_file':str(text),'profile_path':str(n/'profile.json'),'ffprobe':str(n/'ffprobe.exe'),
         'storage':{'disk_reserve_bytes':1000,'admission_path':str(admission),
                    'admission_sha256':hashlib.sha256(admission.read_bytes()).hexdigest(),
                    'approved_output_roots':[str(base)]}}
    root=n/'recordings'/'old';m.atomic(root/'job.json',job,new=True)
    m.atomic(root/'obs-launch.json',{'pid':503,'creation_filetime':100503},new=True)
    m.atomic(root/'failed.json',{'reason':'test overlay exit'},new=True)
    m.atomic(root/'cleanup.json',{'inputs_unbound':True,'unknown_or_global_stop_calls':0,
             'engine_close':{'actual_exit_code':0,'normal_exit_proven':True,'forced_process_calls':0}},new=True)
    request=n/'initial-request.json';m.atomic(request,{'session_id':'old','worker_pid':504,'receipt_root':str(root)},new=True)
    pins={'processes':[{'pid':601,'creation_filetime':100601},{'pid':602,'creation_filetime':100602}]}
    m.atomic(n/'ROOT-ACTUAL-SDK-PROCESSES-PINNED-P42.json',pins,new=True)
    stage='auto_unsettled' if mixed else 'auto_verified'
    state={'completed_cycles':6,'pending_cycle':{'stage':stage,'global_turn':7,'auto_sequence':90},
           'pending_checkpoint':None}
    m.atomic(n/'p42-queue/ROOT-CUMULATIVE-LOOP-STATE.json',state,new=True)
    body={'status':'blocked' if mixed else 'executed','selected_step':None if mixed else 'life-advance'}
    m.atomic(n/'p42-responses/0090-1-result.json',{'result':{'structured_content':body}},new=True)
    halt={'at_utc':stamp,'error_type':'ValueError' if mixed else 'RecordingPaused',
          'original_request':{'sequence':90,'tool':'ck3_auto_turn'} if mixed else
             {'sequence':89,'command':'full_loop','arguments':{'max_turns':30}},
          'original_response':str(n/'p42-responses/0090-1-result.json') if mixed else None}
    m.atomic(n/'ROOT-CURRENT-HALT-P42.json',halt,new=True)
    m.atomic(n/'NEXT-SEQUENCE-P42.json',{'next_sequence':100},new=True)
    config=SimpleNamespace(session=n,sdk_prefix='p42',state_root=n/'watchdog',
        initial_recording_request=request,automatic_source=BASE/'automatic_continuity.py',
        overlay_source=BASE/'fixtures/fake_overlay.py',
        provider_source=BASE/'fixtures/fake_provider.py',
        feeder_template=LIVE/'root_p06_loop_feeder.py',python=Path(sys.executable),
        campaign_label='Offline test',placement_receipt=n/'placement.json')
    platform=FakePlatform(n,job)
    return config,platform

def actual_local_queue(c):
    """Load the real P06 attach/resume methods; stub only guard/process/transport context."""
    source=(LIVE/'root_p06_sdk_queue.py').read_text(encoding='utf-8')
    tree=ast.parse(source);names={'attach_recording_segment','resume_recording_pause'}
    methods=[]
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in names:
            methods.append(node)
    assert len(methods)==2
    module=m.load_source('root_continuous_segment_auto',BASE/'recording_segment_validation.py')
    def write(path,row,**ignored):
        path=Path(str(path).replace('NEXT-SEQUENCE-P06','NEXT-SEQUENCE-P42'))
        m.atomic(path,row,new=not ignored.get('replace',False))
    ns={'Q':c.session/'p42-queue','time':time,'Path':Path,'N':c.session,'R':c.session.parent,'OUTBOX':c.session/'p42-responses',
        'read':m.shared_json,'aware':lambda s:datetime.fromisoformat(s.replace('Z','+00:00')),
        'now':m.utc,'atomic':write}
    node=ast.ClassDef(name='LocalQueue',bases=[],keywords=[],body=methods,decorator_list=[])
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'actual-local-controls','exec'),ns)
    q=ns['LocalQueue']();q.launch=m.shared_json(c.session/'launch.json');q.record_job=c.session/'recordings'/'old'
    q.next_sequence=100;q.args=SimpleNamespace();q.halted={'request':{'command':'full_loop'},'row':None,'response':None}
    q.current_attempt=None;q.held_control=None;q.halt_cause={'error_type':'RecordingPaused'}
    q.recording_paused=True;q.full_loop_state=m.shared_json(c.session/'p42-queue/ROOT-CUMULATIVE-LOOP-STATE.json')
    q.guard=lambda **kw:None
    def consume(request):
        assert request['sequence']==q.next_sequence
        q.next_sequence+=1;m.atomic(c.session/'NEXT-SEQUENCE-P42.json',{'next_sequence':q.next_sequence})
        return request['sequence']
    q.consume_sequence=consume
    return q

def consume_controls(c,q,seen):
    for path in sorted((c.session/'p42-requests').glob('*.json')):
        out=c.session/'p42-responses'/path.name
        if out.exists():continue
        request=m.shared_json(path);name=request['command'];seen.append(name)
        assert 'tool' not in request
        if name=='attach_recording_segment':
            q.attach_recording_segment(request,path)
        elif name=='resume_recording_pause':
            asyncio.run(q.resume_recording_pause(None,request,path))
        elif name=='full_loop':
            assert request['arguments']=={'max_turns':1}
            state=m.shared_json(c.session/'p42-queue/ROOT-CUMULATIVE-LOOP-STATE.json')
            original=state['pending_cycle'];assert original['stage']=='auto_verified'
            m.atomic(c.session/'p42-queue/CUMULATIVE-TURN-000007.json',
                     {**original,'after_metrics_response':'offline-new-readonly-metrics.json'})
            state.update(completed_cycles=7,pending_cycle=None)
            m.atomic(c.session/'p42-queue/ROOT-CUMULATIVE-LOOP-STATE.json',state)
            sequence=q.consume_sequence(request)
            m.atomic(out,{'request':request,'result':{'is_error':False,'structured_content':{
                'status':'bounded_loop_finished','cumulative_cycles':7,
                'same_SDK_continuation_available':True,'next_sequence':q.next_sequence}}},new=True)
        else:raise AssertionError(name)

def test_regular_recovery():
    with tempfile.TemporaryDirectory(dir=BASE,prefix='offline-') as temp:
        c,p=fixture(Path(temp));a=m.ActualAdapter(c,p);q=actual_local_queue(c)
        s=RecoverySupervisor(a,session_root=c.session);seen=[]
        progress=s.drive()
        assert progress.status=='error' and 'retired' in progress.reason
        assert not p.launches and not list((c.session/'p42-requests').iterdir())
        assert a.journal['current_request']==str(c.initial_recording_request)

def test_attach_only_business_halt():
    with tempfile.TemporaryDirectory(dir=BASE,prefix='offline-') as temp:
        c,p=fixture(Path(temp),mixed=True);a=m.ActualAdapter(c,p);q=actual_local_queue(c)
        s=RecoverySupervisor(a,session_root=c.session);assert s.drive().stage=='sdk_guard'
        before=m.shared_json(c.session/'p42-queue/ROOT-CUMULATIVE-LOOP-STATE.json');seen=[]
        with pytest.raises(RuntimeError,match='retired'):a.drive_attach_only(s)
        assert not seen and not p.launches
        assert m.shared_json(c.session/'p42-queue/ROOT-CUMULATIVE-LOOP-STATE.json')==before
        assert a.observe().sdk.halt_cause=='ValueError'

def test_feeder_exclusion_and_unknown_launch():
    with tempfile.TemporaryDirectory(dir=BASE,prefix='offline-') as temp:
        c,p=fixture(Path(temp));p.old_feeder_alive=True;a=m.ActualAdapter(c,p)
        s=RecoverySupervisor(a,session_root=c.session);assert s.drive().status=='error'
        assert not p.launches and not list((c.session/'p42-requests').iterdir())
        p.old_feeder_alive=False;p.fail_launch=True
        assert s.drive().status=='error'
        assert not p.launches
        b=m.ActualAdapter(c,p);t=RecoverySupervisor(b,session_root=c.session)
        assert t.drive().status=='error'
        assert not p.launches  # Retirement cannot be bypassed after watchdog restart.

def test_shared_reader_allows_replace():
    with tempfile.TemporaryDirectory(dir=BASE,prefix='offline-') as temp:
        path=Path(temp)/'state.json';m.atomic(path,{'n':0},new=True)
        for n in range(20):
            assert m.shared_json(path)['n']==n
            m.atomic(path,{'n':n+1})
        assert m.shared_json(path)['n']==20

if __name__=='__main__':
    rows=[]
    for test in [test_regular_recovery,test_attach_only_business_halt,
                 test_feeder_exclusion_and_unknown_launch,test_shared_reader_allows_replace]:
        test();rows.append({'name':test.__name__,'status':'GREEN'});print('GREEN',test.__name__)
    result={'status':'GREEN','offline_only':True,'real_local_queue_methods':['attach_recording_segment','resume_recording_pause'],
            'legacy_panel_recovery_rejected_before_launch':True,
            'settle_transport':'simulated successful full_loop(max_turns=1); no live Game/MCP/OBS',
            'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'tests':rows}
    print(json.dumps(result))
