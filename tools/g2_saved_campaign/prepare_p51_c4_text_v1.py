"""Emit only the saved61 C4 text/presentation generation; never apply or launch."""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

CAPTURE = '950d156551da3579ee6902a1c945e5a343bffecb4addcff9cee86249f99b2161'
NO_MOVE = '74c9f4ce9d800dd5d51159ca8080035f2abd159fcdaf0d42a531f624cd9eb204'

OWNER = '''"""Start one C4 text owner and recording from the already placed saved61 map.

No Game launch, placement, menu navigation, SDK start or pixel admission.
Keep this original owner alive until normal publisher STOP and kernel exit0.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys

P=Path(__file__).resolve().parent
N=P.parent

def read(path):
    data=Path(path).read_bytes()
    if len(data)>131072:raise ValueError('Finite C4 metadata required')
    return json.loads(data)

def checked_sources():
    manifest=read(P/'SOURCE-PINS-C4.json')
    for ref in manifest['files']:
        path=Path(ref['path']);raw=path.read_bytes()
        if len(raw)!=ref['bytes'] or hashlib.sha256(raw).hexdigest()!=ref['sha256']:
            raise ValueError('Exact C4 source differs: '+str(path))
    return manifest

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--current-request',type=Path,required=True)
    parser.add_argument('--ffprobe',type=Path,required=True)
    args=parser.parse_args()
    checked_sources()
    current=args.current_request.resolve()
    if current!=N/'CURRENT-REQUEST-P37.json':raise ValueError('Exact shared monotonic request view required')
    sys.path.insert(0,str(N))
    from root_decision_text_api_c4 import load_api,started_reference
    api=load_api(N)
    import hotfix_provider as provider
    if provider.capture.decision_publisher_api() is not api:raise ValueError('Capture uses another publisher source')
    launch_path=N/'ROOT-ACTUAL-GAME-LAUNCH-C4.json'
    placement_path=N/'ROOT-GAME-PLACEMENT-C4.json'
    launch,placement=read(launch_path),read(placement_path)
    profile_path=N/'ROOT-OBS-PROFILE-C4.json';profile=read(profile_path)
    if (placement.get('status')!='GREEN' or placement.get('foreground_unchanged') is not True
            or placement.get('current_desktop_unchanged') is not True
            or placement.get('pid')!=launch.get('pid')
            or placement.get('creation_filetime')!=launch.get('creation_filetime')
            or launch.get('old_save_loaded') is not True or launch.get('load_save_name')!='xar_checkpoint'
            or launch.get('pid')==214568 or profile.get('continuous') is not True
            or any(profile.get(key) is not None for key in ('deadline_utc','max_output_bytes'))
            or Path(profile['recording_root']).resolve()!=N/'recordings'):
        raise ValueError('Actual C4 loaded-save Game/placement/continuous profile differs')
    config_path=N/'decision-text-publisher-config-c4.json'
    config={'schema':api.SCHEMA,'machine_id':read(N/'STORAGE-ADMISSION.json')['machine_id'],
        'session':str(N),'state_root':str(N/'decision-text-publisher-c4'),
        'decision_text_file':str(N/'live-decision-c4.txt'),'current_request_path':str(current),
        'feed_root':str(N/'responses'),'qualification_only':False,
        'game':{'pid':launch['pid'],'creation_filetime':launch['creation_filetime'],
            'creation_date':launch['creation_date'],'hwnd':placement['hwnd'],
            'desktop_id':placement['target_desktop_id']},'game_launch_receipt':api.pin(launch_path)}
    paths=(config_path,N/'ROOT-DECISION-TEXT-PUBLISHER-BINDING-C4.json',
        N/'ROOT-OBS-RECORDING-REQUESTED-C4.json',N/'ROOT-CURRENT-OBS-RECORDING-REQUESTED-C4.json',
        N/'decision-text-publisher-c4',N/'live-decision-c4.txt')
    if any(path.exists() for path in paths):raise FileExistsError('New C4 owner outputs required; unknown launch is never retried')
    api.atomic(config_path,config,new=True)
    owner=api.PublisherOwner(config_path)
    try:
        owner.start();reference=owner.started()
        owner.seal_binding(N/'ROOT-DECISION-TEXT-PUBLISHER-BINDING-C4.json')
        if started_reference(N,api)!=reference:raise ValueError('C4 actual retained publisher binding differs')
        request=provider.capture.launch_recording(profile_path,N/'recordings',launch['pid'],placement['hwnd'],None,
            launch_receipt=launch_path,ffprobe=args.ffprobe,placement_receipt=placement_path,
            decision_publisher_receipt=Path(reference['path']),continuous=True)
        request.update(capture_admission_stage='saved_map',map_ready_claimed=False,
            generation='C4',saved_checkpoint_opening=True)
        api.atomic(N/'ROOT-OBS-RECORDING-REQUESTED-C4.json',request,new=True)
        api.atomic(N/'ROOT-CURRENT-OBS-RECORDING-REQUESTED-C4.json',request,new=True)
        print(json.dumps({'state':'C4_recording_requested_retained_owner','request':request,
            'publisher_started':reference,'pixel_admitted':False}),flush=True)
    finally:
        # Do not lose custody or stop the publisher on a later capture failure.
        # The supervisor requests STOP only after actual OBS unbound; this
        # original owner then consumes its own retained child handle and exit0.
        if owner.process is not None:
            owner.process.wait()
            proof=owner.close()
            print(json.dumps({'publisher_normal_closed':proof}),flush=True)

if __name__=='__main__':main()
'''

def bounded(path):
    raw=Path(path).read_bytes()
    if len(raw)>131072:raise ValueError('Bounded C4 producer source only: '+str(path))
    return raw

def pin(path):
    raw=bounded(path)
    return {'path':str(Path(path).resolve()),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def replace_once(source, old, new):
    if source.count(old)!=1:raise ValueError('Exact C4 source seam missing: '+old)
    return source.replace(old,new)

def transform_feed(source):
    tree=ast.parse(source)
    function=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='publish_before_submit')
    first=next(node for node in function.body if isinstance(node,ast.Assign)
        and any(isinstance(item,ast.Name) and item.id=='payload' for item in node.targets))
    if "if output.exists(): raise FileExistsError('this decision was already published; no action replay')" not in source:
        raise ValueError('Expected actual C3 single-slot callback source')
    lines=source.splitlines(True)
    tail=('    from root_decision_text_api_c4 import load_api, started_reference\n'
        '    api=load_api(N)\n'
        '    api.publish_callback_observation(row,started_reference(N,api),actual_observation=observation)\n'
        '    return None\n')
    result=''.join(lines[:first.lineno-1])+tail+''.join(lines[function.end_lineno:])
    return replace_once(result,"N/'ROOT-ACTUAL-GAME-LAUNCH.json'","N/'ROOT-ACTUAL-GAME-LAUNCH-C4.json'")

def emit(runtime, output, public_commit, machine_id):
    runtime=runtime.resolve(strict=True);output=output.resolve()
    if output.exists() or output.is_relative_to(runtime):raise ValueError('New external review required')
    repo=Path(__file__).resolve().parents[2]
    commit=subprocess.check_output(['git','rev-parse',public_commit+'^{commit}'],cwd=repo,text=True).strip()
    def public(relative):
        raw=subprocess.check_output(['git','show',commit+':'+relative],cwd=repo)
        if len(raw)>131072:raise ValueError('Finite public source only')
        return raw
    template=ast.parse(public('tools/g2_saved_campaign/migrate_p51_decision_text_v20261019.py'))
    literals={node.targets[0].id:ast.literal_eval(node.value) for node in template.body
        if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name)
        and node.targets[0].id in ('API','RELAY','SEGMENT')}
    api=literals['API']
    for old,new in [('decision-text-publisher/CURRENT-INPUT.json','decision-text-publisher-c4/CURRENT-INPUT.json'),
        ('ROOT-DECISION-TEXT-PROVIDER.json','ROOT-DECISION-TEXT-PROVIDER-C4.json'),
        ('presentation/g2_saved_campaign','presentation-c4/g2_saved_campaign'),
        ('ROOT-DECISION-TEXT-PUBLISHER-BINDING.json','ROOT-DECISION-TEXT-PUBLISHER-BINDING-C4.json')]:
        api=replace_once(api,old,new)
    values={'root_decision_text_api_c4.py':api.encode(),
        'root_p37c4_compact_decision_feed.py':transform_feed(bounded(runtime/'root_p37_compact_decision_feed.py').decode('utf-8-sig')).encode(),
        'root_p37c4_overlay_relay.py':literals['RELAY'].replace('root_decision_text_api','root_decision_text_api_c4').encode(),
        'root_continuous_segment_auto_c4.py':literals['SEGMENT'].replace('root_decision_text_api','root_decision_text_api_c4').encode(),
        'p51_decision_text_shutdown_c4.py':public('tools/g2_saved_campaign/p51_decision_text_shutdown.py').replace(b'root_decision_text_api',b'root_decision_text_api_c4').replace(b'ROOT-DECISION-TEXT-PUBLISHER-BINDING.json',b'ROOT-DECISION-TEXT-PUBLISHER-BINDING-C4.json'),
        'presentation-c4/start_saved_map_c4.py':OWNER.encode()}
    inputs=[pin(runtime/'root_p37_compact_decision_feed.py'),pin(Path(__file__))]
    for name in ('decision_text_publisher','decision_text_view','decision_text_admission','automatic_continuity'):
        values['presentation-c4/g2_saved_campaign/'+name+'.py']=public('tools/g2_saved_campaign/'+name+'.py')
    for name,expected in [('ck3_obs_capture.py',CAPTURE),('obs_owned_desktop.py',NO_MOVE),
        ('hotfix_provider.py',None),('ck3_mod_acceptance_recorder.py',None),('decision_overlay_window.py',None)]:
        source=runtime/'presentation'/name;raw=bounded(source);reference=pin(source)
        if expected is not None and reference['sha256']!=expected:raise ValueError('Adopted no-Move capture source changed')
        inputs.append(reference);values['presentation-c4/'+name]=raw
    output.mkdir();files=[]
    for relative,raw in values.items():
        ast.parse(raw,filename=relative)
        target=output/relative;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(raw)
        files.append(pin(target)|{'relative_path':relative,'install_path':str(runtime/relative)})
    sources={name:{'path':str(runtime/'presentation-c4/g2_saved_campaign'/(name+'.py')),
        'bytes':len(values['presentation-c4/g2_saved_campaign/'+name+'.py']),
        'sha256':hashlib.sha256(values['presentation-c4/g2_saved_campaign/'+name+'.py']).hexdigest()}
        for name in ('decision_text_publisher','decision_text_view','decision_text_admission','automatic_continuity')}
    provider={'schema':'xar.p51.decision-provider-source/v1','machine_id':machine_id,
        'generation':'C4','public_commit':commit,'sources':sources}
    target=output/'ROOT-DECISION-TEXT-PROVIDER-C4.json'
    target.write_text(json.dumps(provider,indent=2),encoding='utf-8')
    files.append(pin(target)|{'relative_path':target.name,'install_path':str(runtime/target.name)})
    manifest={'schema':'xar.p51-c4-source-pins/v1','machine_id':machine_id,
        'files':[{key:value for key,value in row.items() if key in ('bytes','sha256')}|{'path':row['install_path']}
            for row in files]}
    target=output/'presentation-c4/SOURCE-PINS-C4.json'
    target.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    record={'schema':'xar.p51-c4-text-source-review/v1','status':'SOURCE_ONLY_OWNER_APPLY_REQUIRED',
        'machine_id':machine_id,'observed_at_utc':datetime.now(timezone.utc).isoformat(),'public_commit':commit,
        'inputs':inputs,'files':files,'manifest':pin(target),'runtime_mutations':0,
        'Game_OBS_Desktop_Native_calls':0,'source_process_launches':0,
        'consumer_imports':{'root_decision_text_api':'root_decision_text_api_c4',
            'root_p37_compact_decision_feed':'root_p37c4_compact_decision_feed',
            'root_p37_overlay_relay':'root_p37c4_overlay_relay',
            'root_continuous_segment_auto':'root_continuous_segment_auto_c4',
            'p51_decision_text_shutdown':'p51_decision_text_shutdown_c4'},
        'current_views':{'launch':'ROOT-ACTUAL-GAME-LAUNCH-C4.json','placement':'ROOT-GAME-PLACEMENT-C4.json',
            'profile':'ROOT-OBS-PROFILE-C4.json','provider':'ROOT-DECISION-TEXT-PROVIDER-C4.json',
            'publisher_binding':'ROOT-DECISION-TEXT-PUBLISHER-BINDING-C4.json',
            'publisher_state':'decision-text-publisher-c4','decision_text':'live-decision-c4.txt',
            'current_request':'CURRENT-REQUEST-P37.json','result_outbox':'p37-responses',
            'request':'ROOT-OBS-RECORDING-REQUESTED-C4.json',
            'current_recording':'ROOT-CURRENT-OBS-RECORDING-REQUESTED-C4.json',
            'first_frame_admission':'ROOT-SAVED-MAP-RECORDING-ADMITTED-C4.json',
            'map_admission':'ROOT-CAMPAIGN-MAP-ADMITTED-C4.json'},
        'saved_map_pixel_admission':{'schema':'xar.ck3.decision-text-first-frame/v1','stage':'saved_map',
            'requires_actual_root_review':['Game_map_visible','decision_text_visible',
                'before_selection_game_pixels_reviewed','before_selection_decision_pixels_reviewed'],
            'legacy_blue_window_visible':False,'frame':'Post-start frozen Game+scene byte pins inside the new UUID job root',
            'publisher_started':'Exact new C4 STARTED pin, not the old C3 binding',
            'do_not_copy_old_claims':['unrecorded_zero_day_navigation','recording_started_before_first_AUTO',
                'actual_zero_day_baseline','frontend_visible','main_menu_pixels_reviewed'],
            'verify':'load_api(N,decision_text_admission).verify_segment with C4 launch/new UUID and first_frame_admission'},
        'required_before_use':['Owner independently verifies new Game+saved61 checkpoint+paused map+placement and fresh storage/profile.',
            'Owner applies all exact outputs to their install_path, including the separate SOURCE-PINS-C4.json. Never overwrite C3 sources or receipts.',
            'Launch start_saved_map_c4.py using the actual base Python313 and existing explicit dependency environment, --current-request TARGET/CURRENT-REQUEST-P37.json --ffprobe existing_ffprobe.exe.',
            'Retain that owner; it starts publisher once and requests a new recording UUID, no placement/menu/Robert Start/SDK calls.',
            'Wait for actual started.json, final foreground guard and post-start frozen Game+scene pair. Root actual pixel review then public FIRST_SCHEMA saved_map admission uses -C4 launch/placement/request paths.',
            'Fresh C4 queue+entry and saved61 cold queue helper must consume C4 API/segment/relay/feed/shutdown imports; do not alias old C3 globals or reuse old admissions.',
            'TEXT_PUBLISHED only proves exact text publication. Real C4 OBS Game/text pixels, new cold SEM/CAP and saved61 material restore are independent gates.',
            'Normal close order remains SDK settle, OBS normal stop+actual inputs unbound, publisher STOP+original owner exit0, Game close.']}
    (output/'REVIEW.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    return record

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--public-commit',required=True);parser.add_argument('--machine-id',required=True)
    args=parser.parse_args();result=emit(args.runtime,args.output,args.public_commit,args.machine_id)
    print(json.dumps({'status':result['status'],'output':str(args.output),'files':len(result['files'])}))
