"""Create-only display sources from the frozen C6 ordinal/shared-I/O provider.

Emission never writes the target runtime or starts a process. The generated
owner is a future runtime-owner entry point; Game launch/cold restore and pixel
admission remain separate operations.
"""
from __future__ import annotations
import argparse,ast,hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path

# Individual hashes come from this exact frozen manifest, never current HEAD.
PINS = (
 'root_decision_text_api_c6.py','root_p37c6_overlay_relay.py',
 'root_p37c6_compact_decision_feed.py','root_continuous_segment_auto_c6.py',
 'p51_decision_text_shutdown_c6.py','presentation-c6/ck3_obs_capture.py',
 'presentation-c6/obs_owned_desktop.py','presentation-c6/hotfix_provider.py',
 'presentation-c6/decision_overlay_window.py','presentation-c6/ck3_mod_acceptance_recorder.py',
 'presentation-c6/g2_saved_campaign/decision_text_publisher.py',
 'presentation-c6/g2_saved_campaign/decision_text_view.py',
 'presentation-c6/g2_saved_campaign/decision_text_admission.py',
 'presentation-c6/g2_saved_campaign/automatic_continuity.py',
)
MANIFEST = 'e4b6825e91b6217530d694eb99bcc02b9f8dbcdec5d00f2ea3d9a5a68bc48a64'
PROVIDER = '4fe6a6a1f0e32bd26479e41569035ce14b0617a1a3a64092a88928b749a637ed'

OWNER = '''"""Retained new-Game publisher/OBS owner; no Game or SDK launch."""
import argparse,importlib,json,sys
from pathlib import Path
SPEC=__SPEC__
P=Path(__file__).resolve().parent
N=P.parent

def require(ok,why):
    if not ok:raise ValueError('new-Game display owner: '+why)

def read(path):
    raw=Path(path).read_bytes()
    require(len(raw)<=131072,'finite metadata required')
    return json.loads(raw)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('game-launch','placement','obs-profile','current-request','job-root','ffprobe'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--game-pid',type=int,required=True)
    parser.add_argument('--game-birth',type=int,required=True)
    a=parser.parse_args()
    require(str(N.resolve())==SPEC['target_runtime'],'exact new source runtime required')
    import hashlib
    pins=read(P/SPEC['source_manifest'])
    require(pins['machine_id']==SPEC['machine_id'],'machine source binding differs')
    for ref in pins['files']:
        raw=Path(ref['path']).read_bytes()
        require(len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256'],'exact emitted source differs')
    for value,key in ((a.game_launch,'launch'),(a.placement,'placement'),(a.obs_profile,'profile')):
        require(value.resolve()==N/SPEC[key],'new generation receipt path differs: '+key)
    require(a.current_request.resolve()==N/'CURRENT-REQUEST-P37.json','shared monotonic request view required')
    launch,placement,profile=read(a.game_launch),read(a.placement),read(a.obs_profile)
    require(a.game_pid>0 and a.game_birth>0 and launch['pid']==a.game_pid
        and launch['creation_filetime']==a.game_birth
        and placement['pid']==a.game_pid and placement['creation_filetime']==a.game_birth
        and placement['status']=='GREEN' and placement['foreground_unchanged'] is True
        and placement['current_desktop_unchanged'] is True,'actual new Game/placement tuple differs')
    require([a.game_pid,a.game_birth]!=SPEC['previous_Game_tuple'],'new physical Game required; old C6 hot identity is not authority')
    require(profile.get('continuous') is True and Path(profile['recording_root']).resolve()==a.job_root.resolve(),
        'actual new continuous profile/job root differs')
    config_path=N/SPEC['config'];binding=N/SPEC['binding']
    outputs=(config_path,binding,N/SPEC['state'],N/SPEC['text'],N/SPEC['requested'],N/SPEC['current_recording'])
    require(not any(p.exists() for p in outputs),'new generation outputs required; no launch retry')
    sys.path.insert(0,str(N))
    api_module=importlib.import_module(SPEC['api_module'])
    api=api_module.load_api(N)
    import hotfix_provider as provider
    require(provider.capture.decision_publisher_api() is api,'capture uses a different publisher source')
    require(api.process_identity(a.game_pid)['creation_filetime']==a.game_birth,'actual Game birth differs')
    config={'schema':api.SCHEMA,'machine_id':SPEC['machine_id'],'session':str(N),
        'state_root':str(N/SPEC['state']),'decision_text_file':str(N/SPEC['text']),
        'current_request_path':str(a.current_request.resolve()),'feed_root':str(N/'responses'),
        'qualification_only':False,'game':{'pid':a.game_pid,'creation_filetime':a.game_birth,
            'creation_date':launch['creation_date'],'hwnd':placement['hwnd'],
            'desktop_id':placement['target_desktop_id']},'game_launch_receipt':api.pin(a.game_launch)}
    api.atomic(config_path,config,new=True)
    owner=api.PublisherOwner(config_path)
    try:
        owner.start();reference=owner.started();owner.seal_binding(binding)
        require(api_module.started_reference(N,api)==reference,'new independent STARTED binding differs')
        request=provider.capture.launch_recording(a.obs_profile,a.job_root,a.game_pid,placement['hwnd'],None,
            launch_receipt=a.game_launch,ffprobe=a.ffprobe,placement_receipt=a.placement,
            decision_publisher_receipt=Path(reference['path']),continuous=True)
        request.update(capture_admission_stage='saved_map',map_ready_claimed=False,generation=SPEC['generation'])
        api.atomic(N/SPEC['requested'],request,new=True)
        api.atomic(N/SPEC['current_recording'],request,new=True)
        print(json.dumps({'state':'new_Game_recording_requested_retained_owner',
            'publisher_started':reference,'request':request,'pixel_admitted':False}),flush=True)
    finally:
        # The original owner keeps its child handle. Runtime requests STOP only
        # after OBS normal exit/unbound; no capture error silently kills it.
        if owner.process is not None:
            owner.process.wait()
            print(json.dumps({'publisher_normal_closed':owner.close()}),flush=True)

if __name__=='__main__':main()
'''


def require(ok, why):
    if not ok:raise ValueError('new-Game display source: '+why)


def pin(raw,path):
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def read_checked(path,digest):
    require(path.stat().st_size<=131072,'bounded source required')
    raw=path.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==digest,'frozen C6 source differs: '+str(path))
    return raw


def once(source,old,new):
    require(source.count(old)==1,'exact current source seam missing: '+old)
    return source.replace(old,new,1)


def emit(source_runtime, target_runtime, output, *, generation, machine_id):
    source_runtime=Path(source_runtime).resolve(strict=True)
    target_runtime=Path(target_runtime).resolve();output=Path(output).resolve()
    require(re.fullmatch(r'[A-Z][A-Z0-9]{1,15}',generation) and generation!='C6','explicit unused generation required')
    require(not output.exists() and not output.is_relative_to(source_runtime)
        and not output.is_relative_to(target_runtime),'new external review output required')
    manifest_raw=read_checked(source_runtime/'presentation-c6/SOURCE-PINS-C6.json',MANIFEST)
    old_provider=json.loads(read_checked(source_runtime/'ROOT-DECISION-TEXT-PROVIDER-C6.json',PROVIDER))
    require(old_provider['machine_id']==machine_id,'source machine identity differs')
    refs={Path(ref['path']).resolve():ref for ref in json.loads(manifest_raw)['files']}
    sources={};inputs=[]
    for name in PINS:
        path=source_runtime/name
        require(path in refs,'source absent from frozen C6 manifest')
        digest=refs[path]['sha256'];raw=read_checked(path,digest)
        require(path in refs and refs[path]['bytes']==len(raw) and refs[path]['sha256']==digest,'C6 manifest pin differs')
        sources[name]=raw;inputs.append(pin(raw,path))
    old_config_path=source_runtime/'decision-text-publisher-config-c6.json'
    require(old_config_path.stat().st_size<=32768,'finite old publisher identity config required')
    old_config=old_config_path.read_bytes();old_game=json.loads(old_config)['game']
    require(type(old_game.get('pid')) is int and type(old_game.get('creation_filetime')) is int,
        'original C6 physical Game tuple absent')
    inputs.append(pin(old_config,old_config_path))
    lower=generation.lower();presentation='presentation-'+lower
    api_module='root_decision_text_api_'+lower
    spec={'generation':generation,'machine_id':machine_id,'target_runtime':str(target_runtime),
        'previous_Game_tuple':[old_game['pid'],old_game['creation_filetime']],
        'api_module':api_module,'source_manifest':'SOURCE-PINS-'+generation+'.json',
        'launch':'ROOT-ACTUAL-GAME-LAUNCH-'+generation+'.json','placement':'ROOT-GAME-PLACEMENT-'+generation+'.json',
        'profile':'ROOT-OBS-PROFILE-'+generation+'.json','config':'decision-text-publisher-config-'+lower+'.json',
        'state':'decision-text-publisher-'+lower,'text':'live-decision-'+lower+'.txt',
        'binding':'ROOT-DECISION-TEXT-PUBLISHER-BINDING-'+generation+'.json',
        'requested':'ROOT-OBS-RECORDING-REQUESTED-'+generation+'.json',
        'current_recording':'ROOT-CURRENT-OBS-RECORDING-REQUESTED-'+generation+'.json',
        'first_admission':'ROOT-SAVED-MAP-RECORDING-ADMITTED-'+generation+'.json',
        'map_admission':'ROOT-CAMPAIGN-MAP-ADMITTED-'+generation+'.json'}
    api=sources['root_decision_text_api_c6.py'].decode()
    for old,new in (('decision-text-publisher-c6/CURRENT-INPUT.json',spec['state']+'/CURRENT-INPUT.json'),
        ('ROOT-DECISION-TEXT-PROVIDER-C6.json','ROOT-DECISION-TEXT-PROVIDER-'+generation+'.json'),
        ('presentation-c6/g2_saved_campaign',presentation+'/g2_saved_campaign'),
        ('ROOT-DECISION-TEXT-PUBLISHER-BINDING-C6.json',spec['binding'])):
        api=once(api,old,new)
    values={api_module+'.py':api.encode()}
    for old,new in (('root_p37c6_overlay_relay.py','root_p37'+lower+'_overlay_relay.py'),
                    ('root_continuous_segment_auto_c6.py','root_continuous_segment_auto_'+lower+'.py'),
                    ('root_p37c6_compact_decision_feed.py','root_p37'+lower+'_compact_decision_feed.py')):
        text=once(sources[old].decode(),'root_decision_text_api_c6',api_module)
        if 'compact_decision' in old:text=once(text,'ROOT-ACTUAL-GAME-LAUNCH-C4.json',spec['launch'])
        values[new]=text.encode()
    shutdown=once(sources['p51_decision_text_shutdown_c6.py'].decode(),'root_decision_text_api_c6',api_module)
    shutdown=once(shutdown,'ROOT-DECISION-TEXT-PUBLISHER-BINDING-C6.json',spec['binding'])
    values['p51_decision_text_shutdown_'+lower+'.py']=shutdown.encode()
    for name,raw in sources.items():
        if name.startswith('presentation-c6/'):
            values[presentation+name[len('presentation-c6'):]]=raw
    values[presentation+'/start_new_game_display.py']=OWNER.replace('__SPEC__',repr(spec),1).encode()
    provider_name='ROOT-DECISION-TEXT-PROVIDER-'+generation+'.json'
    provider={'schema':old_provider['schema'],'machine_id':machine_id,'generation':generation,
        'source_basis':'Frozen C6 current ordinal/shared-I/O bytes; new physical namespace',
        'sources':{name:pin(values[presentation+'/g2_saved_campaign/'+name+'.py'],
            target_runtime/presentation/'g2_saved_campaign'/(name+'.py')) for name in old_provider['sources']}}
    values[provider_name]=(json.dumps(provider,indent=2)+'\n').encode()
    require(not any((target_runtime/name).exists() for name in values),'target namespace already exists')
    for name,raw in values.items():
        if name.endswith('.py'):ast.parse(raw,filename=name)
    files=[pin(raw,target_runtime/name)|{'relative_path':name} for name,raw in values.items()]
    values[presentation+'/'+spec['source_manifest']]=(json.dumps({'machine_id':machine_id,'files':files},indent=2)+'\n').encode()
    output.mkdir(parents=True)
    for name,raw in values.items():
        p=output/name;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as stream:stream.write(raw)
    review={'schema':'xar.new-Game-display-source-review/v1','status':'SOURCE_ONLY_OWNER_APPLY_REQUIRED',
        'machine_id':machine_id,'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'inputs':inputs,'files':files,'spec':spec,'Game_Desktop_Process_calls':0,'runtime_writes':0,
        'required_after_apply':['New physical Game launch/placement/profile and explicit PID/birth; no old C6 STARTED/job reuse.',
            'Run the retained owner with all explicit CLI arguments; its new config/state/text/binding/request outputs must be absent.',
            'Original owner retains child custody. Actual started/pixels/saved_map admission/cold SEM+CAP remain independent.',
            'SDK entry must import the new feed/relay/segment; score observer and Native29 cold checkpoint binding are separate.',
            'Normal close: SDK settle, OBS normal exit/unbound, publisher STOP and retained-owner exit0.']}
    with (output/'REVIEW.json').open('x',encoding='utf-8') as stream:json.dump(review,stream,indent=2)
    return review


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source-runtime','target-runtime','output'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--generation',required=True);parser.add_argument('--machine-id',required=True)
    a=parser.parse_args();r=emit(a.source_runtime,a.target_runtime,a.output,generation=a.generation,machine_id=a.machine_id)
    print(json.dumps({'status':r['status'],'files':len(r['files']),'output':str(a.output)}))


if __name__=='__main__':main()
