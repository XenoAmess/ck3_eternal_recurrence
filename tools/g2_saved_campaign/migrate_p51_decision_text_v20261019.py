"""Emit a create-only P51 text-publisher migration for the runtime owner to review.

This tool never applies to candidate/runtime inputs and never starts a runtime
process, window, OBS, SDK or Game. It reads public bytes with Git show.
"""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

REFERENCE = 'd90d5e79ac7d22b3376ca70f3fccebd3faef516f'
LIMIT = 1024 * 1024
PLACEMENT_SHA256 = '2f40965ea2af7b010a25750fccaecebb0964d1381d975a8bf4403bdbbae3f493'

API = '''"""Load only this session's exact independent text provider source."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

def load_api(session, name='decision_text_publisher'):
    session=Path(session).resolve()
    manifest=json.loads((session/'ROOT-DECISION-TEXT-PROVIDER.json').read_bytes())
    ref=manifest['sources'][name]
    path=Path(ref['path']).resolve(strict=True)
    if path != session/'presentation/g2_saved_campaign'/(name+'.py'):
        raise ValueError('Independent provider escaped the actual presentation source')
    data=path.read_bytes()
    if len(data)>131072 or len(data)!=ref['bytes'] or hashlib.sha256(data).hexdigest()!=ref['sha256']:
        raise ValueError('Independent provider exact source differs')
    existing=sys.modules.get(name)
    if existing is not None:
        if Path(existing.__file__).resolve()!=path:raise ValueError('Foreign cached decision provider')
        return existing
    if name!='decision_text_publisher':load_api(session)
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    try:spec.loader.exec_module(module)
    except BaseException:
        if sys.modules.get(name) is module:sys.modules.pop(name)
        raise
    return module

def started_reference(session, api):
    binding=api.read(Path(session)/'ROOT-DECISION-TEXT-PUBLISHER-BINDING.json')
    if (binding.get('schema')!='xar.ck3.decision-text-publisher-binding/v1'
            or binding.get('publisher_sources')!=api.source_pins() or binding.get('OBS_draw_ack') is not False):
        raise ValueError('Actual independent publisher binding required')
    reference=binding['publisher_started']
    api.validate_started(reference,machine_id=binding['machine_id'])
    return reference
'''

RELAY = '''"""Publish bounded actual observations and consume exact text-file ACKs."""
import json
import os
from pathlib import Path
import uuid
from root_decision_text_api import load_api, started_reference

OLD_RESPONSES=Path(__file__).resolve().parent/'responses'

def relay_compact(source, compact):
    source=Path(source).resolve();session=OLD_RESPONSES.parent
    if (not source.is_file() or not source.is_relative_to(session) or not isinstance(compact,dict)
            or not (source.name.endswith('-0-plan.json') or source.name.endswith('-1-result.json'))):
        raise ValueError('Actual bounded plan/tool result source required')
    api=load_api(session);reference=started_reference(session,api)
    if source.name.endswith('-0-plan.json'):
        # The real before_submit source keeps its exact sequence filename.
        # No display-only alias can masquerade as the held Service callback.
        if compact.get('source')!='actual GameplayBridgeService.before_submit callback':
            raise ValueError('Actual Service before-submit source required')
        published=source
    else:
        row={**compact,'source_ref':str(source),'source_namespace':source.parent.name}
        payload=json.dumps(row,ensure_ascii=False,separators=(',',':')).encode('utf-8')
        if len(payload)>16384:raise ValueError('Actual display projection exceeds16KiB')
        published=OLD_RESPONSES/(source.parent.name+'-'+source.name)
        if published.exists():raise FileExistsError('Immutable actual display source exists; no replay')
        temporary=published.with_name(published.name+'.'+uuid.uuid4().hex+'.pending')
        try:
            with temporary.open('xb') as stream:stream.write(payload)
            os.rename(temporary,published)
        finally:temporary.unlink(missing_ok=True)
    # This blocks the synchronous before_submit callback until the retained
    # publisher proves this exact observation was written to its bound text.
    # TEXT_PUBLISHED is neither an OBS-drawn nor a business-result receipt.
    ack=api.wait_text_published(published,reference,timeout_seconds=5)
    if ack.get('OBS_draw_ack') is not False or ack.get('business_submission_or_outcome_inferred') is not False:
        raise ValueError('Publication ACK scope differs')
    return published

def error_projection(row):
    result=row.get('result');result=result if isinstance(result,dict) else {}
    messages=[str(row['client_error'])[:2048]] if row.get('client_error') else []
    messages += [block['text'][:2048] for block in result.get('content',[])[:3]
                 if isinstance(block,dict) and block.get('type')=='text' and isinstance(block.get('text'),str)]
    return {'request':row.get('request'),'ended_at_utc':row.get('ended_at_utc'),
            'source':'compact actual SDK error; original response retained',
            'result':{'is_error':True,'structured_content':{'status':'error','message':'\\n'.join(messages)[:6144],
                      'outcome_verified':False,'original_request_replayed':False}}}
'''

SEGMENT = '''"""Use the independent text gate; no retired overlay identity is admitted."""
from root_decision_text_api import load_api

def verify_segment(n,r,launch,root,first_path,read,aware,now):
    return load_api(n,'decision_text_admission').verify_segment(n,r,launch,root,first_path,read,aware,now)
'''

START_BLOCK = '''        api=private_dependencies.capture.decision_publisher_api()
        source_root=PACKAGE/'g2_saved_campaign'
        names=('decision_text_publisher','decision_text_view','decision_text_admission','automatic_continuity')
        helper.write(N/'ROOT-DECISION-TEXT-PROVIDER.json',{'schema':'xar.p51.decision-provider-source/v1',
            'sources':{name:api.pin(source_root/(name+'.py'),131072) for name in names}})
        config_path=N/'decision-text-publisher-config.json'
        config={'schema':api.SCHEMA,'machine_id':helper.read(N/'STORAGE-ADMISSION.json')['machine_id'],
            'session':str(N),'state_root':str(N/'decision-text-publisher'),'decision_text_file':str(decision_text),
            'current_request_path':str(N/('CURRENT-REQUEST-'+args.sdk_prefix.upper()+'.json')),
            'feed_root':str(N/'responses'),'qualification_only':False,
            'game':{'pid':game.pid,'creation_filetime':game.creation_filetime,'creation_date':launch['creation_date'],
                    'hwnd':placement['hwnd'],'desktop_id':DESKTOP1},
            'game_launch_receipt':api.pin(launch_path)}
        helper.write(config_path,config)
        publisher_owner=api.PublisherOwner(config_path)
        publisher_owner.start()
        publisher_started=publisher_owner.started()
        publisher_owner.seal_binding(N/'ROOT-DECISION-TEXT-PUBLISHER-BINDING.json')
        publisher=api.read_text_binding(publisher_started,game=config['game'])
        child=publisher_owner.process
        status.update(state='exact_independent_text_publisher_started',publisher=publisher['publisher'],
            publisher_started=publisher_started,decision_text_file=str(decision_text),creates_legacy_window=False,
            publication_ack_is_OBS_draw_ack=False)
        helper.write(run/'owner.json',status,replace=True)
'''

FRONTEND = '''"""Admit actual Root-reviewed frontend Game and independent text pixels."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ACTIONS={'ck3_activate_frontend_new_game_v1','ck3_activate_frontend_start_1066_bookmark_character_v1'}

def read(path,limit=1024**2):
    data=Path(path).read_bytes()
    if len(data)>limit:raise ValueError('Bounded admission metadata required')
    return json.loads(data)

def pin(path):
    path=Path(path).resolve(strict=True);data=path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--session',type=Path,required=True);p.add_argument('--sdk-prefix',required=True)
    p.add_argument('--review',type=Path,required=True);a=p.parse_args();root=a.session.resolve(strict=True)
    sys.path.insert(0,str(root))
    from root_decision_text_api import load_api
    api=load_api(root);gate=load_api(root,'decision_text_admission')
    launch=read(root/'ROOT-ACTUAL-GAME-LAUNCH.json');request=read(root/'ROOT-OBS-RECORDING-REQUESTED.json')
    job_root=Path(request['receipt_root']).resolve(strict=True)
    if job_root.parent!=root/'recordings' or job_root.name!=request['session_id']:
        raise ValueError('New actual recording root differs')
    job,started,placement=map(read,(job_root/'job.json',job_root/'started.json',root/'ROOT-GAME-PLACEMENT.json'))
    review=read(a.review,32768)
    if (review.get('reviewer')!='/root' or review.get('stage')!='frontend'
            or any(review.get(k) is not True for k in ('main_menu_pixels_reviewed','decision_text_pixels_reviewed',
                'before_selection_game_pixels_reviewed','before_selection_decision_pixels_reviewed'))
            or review.get('legacy_blue_window_visible') is not False
            or review.get('game_pid')!=launch['pid'] or review.get('game_creation_filetime')!=launch['creation_filetime']
            or review.get('recording_session_id')!=job['session_id']
            or placement.get('status')!='GREEN' or placement.get('pid')!=job['pid']
            or placement.get('creation_filetime')!=job['game_creation_filetime'] or placement.get('hwnd')!=job['hwnd']
            or placement.get('target_desktop_id')!=job['desktop_id']
            or placement.get('foreground_unchanged') is not True or placement.get('current_desktop_unchanged') is not True):
        raise ValueError('Actual frontend Game, decision text and placement review differ')
    next_path=root/('NEXT-SEQUENCE-'+a.sdk_prefix.upper()+'.json')
    current=read(next_path).get('next_sequence') if next_path.exists() else 1
    if type(current) is not int or not 1<=current<=256:raise ValueError('Bounded frontend startup cursor required')
    for number in range(1,current+1):
        source=root/(a.sdk_prefix+'-requests')/f'{number:04d}-1-result.json'
        if source.exists() and read(source).get('tool') in ACTIONS:
            raise ValueError('Frontend selection/start submitted before admission')
    first={'schema':gate.FIRST_SCHEMA,'status':'GREEN','stage':'frontend','reviewer':'/root',
        'machine_id':job['decision_text_publisher']['machine_id'],'at_utc':review['at_utc'],
        'game_pid':launch['pid'],'game_creation_filetime':launch['creation_filetime'],'game_creation_date':launch['creation_date'],
        'game_hwnd':job['hwnd'],'managed_desktop_id':job['desktop_id'],
        'recording_session_id':job['session_id'],'recorder_session_id':job['session_id'],'recording_job_root':str(job_root),
        'publisher_started':job['decision_text_publisher_receipt'],'review':pin(a.review),
        'recording_started':pin(job_root/'started.json'),'placement':pin(root/'ROOT-GAME-PLACEMENT.json'),
        'frame':{'at_utc':review['at_utc'],'mutable_latest_frame':False,'game':review['game_frame'],'scene':review['scene_frame']},
        'before_selection_game_pixels_reviewed':True,'before_selection_decision_pixels_reviewed':True,
        'decision_text_visible':True,'legacy_blue_window_visible':False,'frontend_visible':True,
        'main_menu_pixels_reviewed':True,'decision_text_pixels_reviewed':True,
        'recording_started_before_frontend_actions':True,'frontend_actions_submitted_before_admission':0,
        'map_ready_claimed':False,'Game_MCP_OBS_Desktop_calls_by_admission':0}
    target=root/'ROOT-FRONTEND-RECORDING-ADMITTED.json'
    if target.exists():raise FileExistsError('Frontend admission is create-only')
    def admission_read(path,limit=1024**2):
        return first if Path(path).resolve()==target else read(path,limit)
    gate.verify_segment(root,root,launch,job_root,target,admission_read,
        lambda text:datetime.fromisoformat(text.replace('Z','+00:00')),lambda:datetime.now(timezone.utc))
    with target.open('x',encoding='utf-8') as stream:json.dump(first,stream,ensure_ascii=False,indent=2)
    print(json.dumps(pin(target)))

if __name__=='__main__':main()
'''

def replace_once(source, old, new):
    if source.count(old) != 1: raise ValueError('Migration anchor is not unique: '+old[:100])
    return source.replace(old,new,1)

def transform_start(source):
    source=replace_once(source,'OVERLAY_SOURCE = PACKAGE / "live_audience_overlay.py"\nOVERLAY_SHA256 = hashlib.sha256(OVERLAY_SOURCE.read_bytes()).hexdigest()',
                        '# Independent publisher source pins are written only after actual placement.')
    source=replace_once(source,'if (N / "STOP-DECISION-OVERLAY").exists():\n        raise ValueError("explicit overlay STOP is present")',
                        'if (N / "decision-text-publisher/STOP").exists():\n        raise ValueError("explicit text publisher STOP is present")')
    source=replace_once(source,'"session": str(N), "overlay_source_sha256": OVERLAY_SHA256,','"session": str(N), "decision_provider": "independent_text",')
    source=replace_once(source,'child, overlay_pin = None, None','child, publisher_owner = None, None')
    first=source.index('        binding = {"pid": game.pid')
    last=source.index('        spec = importlib.util.spec_from_file_location("clean_frontend_recording_provider"',first)
    source=source[:first]+START_BLOCK+source[last:]
    source=replace_once(source,'overlay_receipt=overlay_receipt, continuous=True,','decision_publisher_receipt=Path(publisher_started["path"]), continuous=True,')
    source=replace_once(source,'game.check();overlay_pin.check();time.sleep(.2)',
                        'game.check();api.validate_started(publisher_started);time.sleep(.2)')
    source=replace_once(source,'status.update(overlay_launcher_exit_code=child.wait(), state="overlay_owner_ended",',
                        'child.wait()\n        status.update(publisher_normal_close=publisher_owner.close(), state="text_publisher_owner_ended",')
    source=replace_once(source,'        if overlay_pin is not None:\n            overlay_pin.close()\n','')
    source=source.replace('overlay owner','independent text publisher owner').replace('overlay/recording children','text publisher/recording children')
    source=transform_used_placement(source,PLACEMENT_SHA256)
    if any(token in source for token in ('NativeOverlay','build_overlay_argv','overlay_hwnd','overlay_pid','overlay_receipt=')):
        raise ValueError('Retired display constructor/identity remains in startup')
    return source

def transform_used_placement(source, expected_sha):
    source=replace_once(source,'''    for path, expected_sha in helper.PINS.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha:
            raise ValueError(f"pinned source changed: {path}")
''','')
    anchor='    from managed_desktop1_placement import place, ProcessGeneration, game_generation'
    return replace_once(source,anchor,anchor+"\n    import managed_desktop1_placement as actual_placement_source\n    if hashlib.sha256(Path(actual_placement_source.__file__).read_bytes()).hexdigest() != "+repr(expected_sha)+":\n        raise ValueError('Actual consumed placement helper differs from reviewed public source')")

def transform_map(source):
    return replace_once(replace_once(source,'"--reviewed-overlay"','"--reviewed-decision-text"'),
        '"decision_overlay_visible": True','"decision_text_visible": True')

def transform_queue(source):
    token='!= "game_decision"'
    if source.count(token)!=3:raise ValueError('Expected exactly3 old queue capture guards')
    source=source.replace(token,'!= "game_decision_text"')
    source=replace_once(source,'first.get("stage") != "main_menu"','first.get("stage") != "frontend"')
    source=replace_once(source,'first.get("decision_overlay_pixels_reviewed")','first.get("decision_text_pixels_reviewed")')
    source=replace_once(source,'receipt.get("decision_overlay_visible")','receipt.get("decision_text_visible")')
    source=replace_once(source,'first.get("schema") != "xar.clean-campaign.frontend-recording-admission/v1"',
                        'first.get("schema") != "xar.ck3.decision-text-first-frame/v1"')
    anchor='            raise ValueError("actual recorded MainMenu and audience overlay admission required")'
    source=replace_once(source,anchor,anchor+'\n        from root_continuous_segment_auto import verify_segment\n        verify_segment(N, R, self.launch, self.record_job, self.args.first_frame_admission, read, aware, now)')
    return source

def port_frontend_fixture(source):
    source=replace_once(source,'import copy\n','import copy\nimport os\nfrom unittest.mock import patch\n')
    source=replace_once(source,'PACK = Path(__file__).resolve().parent',"PACK = Path(os.environ['P51_TEXT_QUALIFICATION_ROOT']).resolve(strict=True)")
    source=replace_once(source,'ROOT = N / "robert30-clean-campaign01/runtime"',"ROOT = Path(os.environ['P51_RUNTIME_SOURCE']).resolve(strict=True)")
    source=replace_once(source,'SDK = N / "sdk-p37-candidate/src"',"SDK = Path(os.environ['P51_SDK_SOURCE']).resolve(strict=True)")
    source=source.replace('"game_decision"','"game_decision_text"').replace('"stage": "main_menu"','"stage": "frontend"')
    source=source.replace('"xar.clean-campaign.frontend-recording-admission/v1"','"xar.ck3.decision-text-first-frame/v1"')
    source=source.replace('"decision_overlay_pixels_reviewed"','"decision_text_pixels_reviewed"').replace('"decision_overlay_visible"','"decision_text_visible"')
    source=replace_once(source,'            write(jobroot / "job.json", job)',
        '''            reference={'path':str(root/'publisher/STARTED.json'),'bytes':10,'sha256':'a'*64}
            job.update(overlay=None,decision_text_publisher_receipt=reference,decision_text_publisher={'machine_id':'synthetic'})
            write(jobroot / "job.json", job)''')
    source=replace_once(source,'            first_path = root / "ROOT-FRONTEND-RECORDING-ADMITTED.json"; write(first_path, first)',
        '''            first.update(publisher_started=reference,before_selection_game_pixels_reviewed=True,
                before_selection_decision_pixels_reviewed=True,decision_text_visible=True,legacy_blue_window_visible=False)
            first_path = root / "ROOT-FRONTEND-RECORDING-ADMITTED.json"; write(first_path, first)''')
    source=replace_once(source,'                cls.__init__(queue, args)',
        '''                # Explicit substituted provider gate: this test covers the
                # actual queue schema consumer, not OS/source/pixel attestation.
                # The strict public gate has its separate source qualification.
                gate_calls=[]
                def fake_provider_gate(*gate_args):
                    actual_job=json.loads((jobroot/'job.json').read_bytes())
                    actual_first=json.loads(first_path.read_bytes())
                    self.assertEqual(actual_job['capture_mode'],'game_decision_text')
                    self.assertIsNone(actual_job['overlay'])
                    self.assertEqual(actual_first['publisher_started'],actual_job['decision_text_publisher_receipt'])
                    self.assertEqual(actual_first['schema'],'xar.ck3.decision-text-first-frame/v1')
                    gate_calls.append('exact_new_schema_consumed_by_actual_queue')
                with patch.dict(sys.modules,{'root_continuous_segment_auto':SimpleNamespace(verify_segment=fake_provider_gate)}):
                    first['schema']='xar.clean-campaign.frontend-recording-admission/v1';write(first_path,first)
                    with self.assertRaises(ValueError):cls.__init__(queue,args)
                    self.assertEqual(gate_calls,[])
                    first['schema']='xar.ck3.decision-text-first-frame/v1';write(first_path,first)
                    cls.__init__(queue, args)
                self.assertEqual(gate_calls,['exact_new_schema_consumed_by_actual_queue'])''')
    source=source.replace('"""Formal queue path on explicit temporary fixtures. No runtime/Driver calls."""',
        '"""Actual new queue schema path with an explicitly substituted provider gate; no runtime/Driver calls."""')
    return source

def emit_amendment(pack, output, repo, machine_id, fixture):
    pack,output,repo=map(lambda p:Path(p).resolve(),(pack,output,repo))
    if output.exists() or output==pack or output.is_relative_to(pack):raise ValueError('New external amendment review required')
    inputs=[];results={};diffs=[]
    transforms={
        'candidate-runtime/root_p37_sdk_queue.py':lambda source:replace_once(source,
            'first.get("schema") != "xar.clean-campaign.frontend-recording-admission/v1"',
            'first.get("schema") != "xar.ck3.decision-text-first-frame/v1"'),
        'candidate-runtime/admit_initial_map.py':transform_map,
    }
    for relative,transform in transforms.items():
        data=(pack/relative).read_bytes();source=data.decode('utf-8-sig').replace('\r\n','\n')
        if len(data)>LIMIT:raise ValueError('Finite source required')
        results[relative]=transform(source).encode();inputs.append({'path':str(pack/relative),**pin(data)})
        diffs.extend(difflib.unified_diff(source.splitlines(True),results[relative].decode().splitlines(True),fromfile='input/'+relative,tofile='review/'+relative))
    data=Path(fixture).read_bytes();source=data.decode('utf-8-sig').replace('\r\n','\n')
    results['test_clean_frontend_text_contract.py']=port_frontend_fixture(source).encode()
    inputs.append({'path':str(Path(fixture).resolve()),**pin(data)})
    # Only actual read/write functions are reused from the historical helper;
    # its five unrelated legacy producer pins are no longer startup inputs.
    relative='candidate-presentation/start_clean_presentation.py';data=(pack/relative).read_bytes()
    source=data.decode('utf-8-sig').replace('\r\n','\n')
    placement=subprocess.check_output(['git','show',REFERENCE+':tools/g2_saved_campaign/managed_desktop1_placement.py'],cwd=repo)
    source=transform_used_placement(source,pin(placement)['sha256'])
    results[relative]=source.encode();inputs.append({'path':str(pack/relative),**pin(data)})
    for relative,data in results.items():ast.parse(data,filename=relative)
    output.mkdir();files=[]
    for relative,data in results.items():
        path=output/relative;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(data)
        files.append({'path':str(path),'relative_path':relative,**pin(data)})
    (output/'changes.diff').write_text(''.join(diffs),encoding='utf-8')
    report={'schema':'xar.p51-text-schema-amendment.v1','machine_id':machine_id,'observed_at_utc':datetime.now(timezone.utc).isoformat(),
        'status':'SOURCE_REVIEW_ONLY_NOT_APPLIED','inputs':inputs,'files':files,'candidate_runtime_mutations':0,
        'runtime_process_calls':0,'git_read_processes':1,'AST_checks':len(files),
        'public_placement_source':{'git_commit':REFERENCE,'path':'tools/g2_saved_campaign/managed_desktop1_placement.py',**pin(placement)},
        'previous_qualification_failure_preserved':True,'strict_public_gate_not_relaxed':True}
    (output/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report

def pin(data):return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def emit(pack, output, repo, machine_id):
    pack,output,repo=map(lambda p:Path(p).resolve(),(pack,output,repo))
    if output.exists() or output==pack or output.is_relative_to(pack):raise ValueError('New external review output required')
    sources={};results={};inputs=[];public=[]
    replacements={
        'candidate-runtime/root_p37_overlay_relay.py':lambda _:RELAY,
        'candidate-runtime/root_continuous_segment_auto.py':lambda _:SEGMENT,
        'candidate-runtime/root_p37_sdk_queue.py':transform_queue,
        'candidate-runtime/admit_initial_map.py':transform_map,
        'candidate-presentation/start_clean_presentation.py':transform_start,
        'candidate-presentation/admit_frontend_recording.py':lambda _:FRONTEND,
        'candidate-presentation/live_audience_overlay.py':lambda _:'"""Retired NativeOverlay entry; no alias is admitted for new recording."""\nraise RuntimeError("Legacy blue decision window retired; use independent decision text publisher")\n',
    }
    for relative,transform in replacements.items():
        data=(pack/relative).read_bytes()
        if len(data)>LIMIT:raise ValueError('Finite migration input exceeded')
        source=data.decode('utf-8-sig').replace('\r\n','\n');sources[relative]=source
        results[relative]=transform(source).encode('utf-8')
        inputs.append({'path':str(pack/relative),'relative_path':relative,**pin(data)})
    results['candidate-runtime/root_decision_text_api.py']=API.encode('utf-8')
    mapping={'tools/ck3_obs_capture.py':'candidate-presentation/ck3_obs_capture.py',
        'tools/ck3_mod_acceptance_recorder.py':'candidate-presentation/ck3_mod_acceptance_recorder.py'}
    for name in ('decision_text_publisher','decision_text_view','decision_text_admission','automatic_continuity'):
        mapping['tools/g2_saved_campaign/'+name+'.py']='candidate-presentation/g2_saved_campaign/'+name+'.py'
    for source,target in mapping.items():
        data=subprocess.check_output(['git','show',REFERENCE+':'+source],cwd=repo)
        if len(data)>LIMIT:raise ValueError('Finite public provider source exceeded')
        results[target]=data;public.append({'git_commit':REFERENCE,'path':source,**pin(data)})
    for relative,data in results.items():ast.parse(data,filename=relative)
    if sum(map(len,results.values()))>512*1024:raise ValueError('Review source budget exceeded512KiB')
    output.mkdir()
    files=[]
    for relative,data in results.items():
        target=output/relative;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(data)
        files.append({'relative_path':relative,'path':str(target),**pin(data)})
    diffs=[]
    for relative,old in sources.items():
        diffs.extend(difflib.unified_diff(old.splitlines(True),results[relative].decode().splitlines(True),
            fromfile='input/'+relative,tofile='review/'+relative))
    (output/'changes.diff').write_text(''.join(diffs),encoding='utf-8')
    report={'schema':'xar.p51-decision-text-migration-review.v1','machine_id':machine_id,
        'observed_at_utc':datetime.now(timezone.utc).isoformat(),'status':'SOURCE_REVIEW_ONLY_NOT_APPLIED',
        'reference_commit':REFERENCE,'pack':str(pack),'inputs':inputs,'public_sources':public,'files':files,
        'candidate_or_runtime_mutations':0,'Game_OBS_Desktop_Native_calls':0,'runtime_process_launches':0,
        'git_read_processes':len(mapping),'producer_git_reads_only':True,'AST_checks':len(files),'qualified_live_or_pixels':False,
        'owner_required_followup':['verify original input pins immediately before copying reviewed files',
            'preserve presentation subdirectory relative paths in finalize/source pins',
            'refresh source pins after owner apply and existing binder/profile work',
            'stop publisher by its decision-text-publisher/STOP and retain original owner exit0 proof',
            'review actual new frontend/gray decision pixels with the new receipt fields']}
    (output/'REVIEW.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pack',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--reference-repo',type=Path,required=True);p.add_argument('--machine-id',required=True)
    p.add_argument('--amendment-fixture',type=Path,help='Emit only the observed schema/map/helper-pin amendment from already migrated candidates')
    a=p.parse_args();r=(emit_amendment(a.pack,a.output,a.reference_repo,a.machine_id,a.amendment_fixture)
        if a.amendment_fixture is not None else emit(a.pack,a.output,a.reference_repo,a.machine_id))
    print(json.dumps({'status':r['status'],'output':str(a.output),'files':len(r['files']),
        'bytes':sum(x['bytes'] for x in r['files']),'reference_commit':r.get('reference_commit',REFERENCE)}))
