"""Read pinned Root files once, then consume the existing military GUI family.

No SDK, driver construction, discovery, game process, DLL or EXE access.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,os,sys,types
from pathlib import Path
from datetime import datetime,timezone
sys.dont_write_bytecode=True

ROOT=Path(__file__).resolve().parent
REPO=Path('D:/workspace/ck3_eternal_recurrence')
CHILD='definition_frontier_continuation_depth8_12'
READS=[]
SEEN_PATHS=set()

def require(ok,reason):
    if not ok:raise ValueError(reason)

def unique(pairs):
    result={}
    for key,value in pairs:
        require(key not in result,'duplicate JSON key: '+key);result[key]=value
    return result

def pointer(value,path):
    require(type(path) is str and (path=='' or path.startswith('/')),'explicit JSON pointer required')
    for token in path.split('/')[1:]:
        token=token.replace('~1','/').replace('~0','~')
        if type(value) is list:
            require(token.isdigit() and str(int(token))==token,'canonical list pointer required')
            value=value[int(token)]
        else:value=value[token]
    return value

def checked_file(spec,role,max_bytes):
    require(type(spec) is dict and all(k in spec for k in ('path','bytes','sha256')),'exact file pin missing: '+role)
    require(type(spec['bytes']) is int and 0<spec['bytes']<=max_bytes,'file size outside explicit input cap: '+role)
    require(type(spec['sha256']) is str and len(spec['sha256'])==64 and all(c in '0123456789abcdef' for c in spec['sha256']),'lowercase SHA required')
    path=Path(spec['path']);key=os.path.normcase(str(path.resolve()))
    require(key not in SEEN_PATHS,'one source path cannot be body-read twice: '+role)
    SEEN_PATHS.add(key);before=path.stat()
    require(before.st_size==spec['bytes'],'pinned file size differs: '+role)
    with path.open('rb') as stream:data=stream.read(spec['bytes']+1)
    after=path.stat()
    require((before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'input changed during read: '+role)
    require(len(data)==spec['bytes'] and hashlib.sha256(data).hexdigest()==spec['sha256'],'pinned bytes/SHA differs: '+role)
    READS.append(dict(role=role,path=path.as_posix(),bytes=len(data),sha256=spec['sha256'],body_read_count=1,hash_and_parse_use_same_bytes=True))
    return json.loads(data,object_pairs_hook=unique)

def load_consumers(repo,expected):
    for name in ('gui_callback_binding_12004_contract.py','gui_refill_receiver_candidates_12004_contract.py'):
        raw=(repo/'ck3_autonomous_player/src/xar_autoplayer/bridge'/name).read_bytes()
        require(name in expected and len(raw)==expected[name]['bytes'] and hashlib.sha256(raw).hexdigest()==expected[name]['sha256'],'production consumer pin differs: '+name)
    for name,paths in [('xar_autoplayer',[repo/'ck3_autonomous_player/src/xar_autoplayer']),('xar_autoplayer.bridge',[repo/'ck3_autonomous_player/src/xar_autoplayer/bridge'])]:
        package=types.ModuleType(name);package.__path__=[str(p) for p in paths];sys.modules[name]=package
    from xar_autoplayer.bridge.gui_callback_binding_12004_contract import SOURCE_RECEIVER_12004,normalize_callback_binding_rows_12004
    from xar_autoplayer.bridge.gui_refill_receiver_candidates_12004_contract import normalize_receiver_frame
    return SOURCE_RECEIVER_12004,normalize_callback_binding_rows_12004,normalize_receiver_frame

def check_literals(raw,checks,role):
    require(type(checks) is dict,'literal checks must be a pointer map: '+role)
    for path,expected in checks.items():
        actual=pointer(raw,path)
        require(type(actual) is type(expected) and actual==expected,'literal differs at '+role+path)

def complete_family(payload):
    return (type(payload) is dict and type(payload.get('widgets')) is list
            and 'callback_binding_source_12004' in payload and 'refill_receiver_frame_12004' in payload
            and 'refill_receiver_public_binding_12004' in payload
            and all(type(w) is dict and 'vtable_rva' in w and 'standard_click_binding_12004' in w for w in payload['widgets']))

def extract(manifest,repo=REPO,max_bytes=64*1024*1024):
    READS.clear()
    SEEN_PATHS.clear()
    require(manifest.get('schema')=='xar.r06.frontier.file-input.v1','manifest schema')
    require(manifest.get('evidence_kind') in ('authored-fixture','existing-live-observation'),'explicit evidence kind required')
    require(type(manifest.get('machine_id')) is str and manifest['machine_id'],'source machine_id required')
    if manifest['evidence_kind']=='existing-live-observation':
        require(type(manifest.get('source_observed_at')) is str and manifest['source_observed_at'],'actual source observation time required')
        datetime.fromisoformat(manifest['source_observed_at'].replace('Z','+00:00'))
    sys.path.insert(0,str(repo))
    from tools.ck3_live_run_id import current_machine_id
    analysis_machine=current_machine_id()
    identity=checked_file(manifest['runtime_identity'],'runtime_identity',1024*1024)
    check_literals(identity,manifest['identity_checks'],'runtime_identity')
    expected=manifest['expected_frame'];public=manifest['expected_public_binding']
    require(set(expected)=={'game_pid','connection_generation','native_revision','played_character_full_id','date_raw'},'expected frame must bind PID/gen/native revision/actor/date')
    require(set(public)=={'snapshot_id','revision','native_revision','episode_run_id'} and public['native_revision']==expected['native_revision'],'exact expected public binding required')
    # Every expected runtime binding is sourced by a Root-specified exact
    # pointer in the independently pinned identity. No path/name inference.
    identity_map=manifest['identity_binding_pointers']
    required={'machine_id','game_pid','connection_generation','played_character_full_id','episode_run_id','process_creation_filetime_100ns'}
    require(set(identity_map)==required,'runtime identity source pointers incomplete')
    values={key:pointer(identity,path) for key,path in identity_map.items()}
    require(values['machine_id']==manifest['machine_id'] and values['episode_run_id']==public['episode_run_id'],'source machine/episode differs')
    require(type(values['process_creation_filetime_100ns']) is int and values['process_creation_filetime_100ns']>0,'actual process creation identity required')
    for key in ('game_pid','connection_generation','played_character_full_id'):
        require(type(values[key]) is type(expected[key]) and values[key]==expected[key],'runtime identity differs: '+key)
    request=checked_file(manifest['request'],'request',1024*1024)
    tool=request.get('tool');arguments=request.get('arguments')
    require((tool=='ck3_inspect_gui_window_tree_v1' and arguments=={'window_kind':'military'}) or (
        tool=='ck3_execute_step' and type(arguments) is dict and arguments.get('step')=='activate-ingame-military-v1'
        and set(arguments)=={'step','expected_revision'} and type(arguments['expected_revision']) is int), 'request is not the existing fixed GUI query/opener')
    endpoint=checked_file(manifest['endpoint'],'endpoint',max_bytes)
    check_literals(endpoint,manifest['response_checks'],'endpoint')
    payload=pointer(endpoint,manifest['endpoint_payload_pointer']);used='endpoint';chosen=endpoint
    if not complete_family(payload) and 'driver' in manifest:
        # Only Root's named exact reference authorizes this fallback. Never
        # recursively search, glob, or follow a path discovered in an artifact.
        check_literals(endpoint,manifest['driver_reference_checks'],'endpoint_driver_reference')
        require(bool(manifest['driver_reference_checks']),'fallback needs exact response-local reference checks')
        driver=checked_file(manifest['driver'],'driver',max_bytes)
        check_literals(driver,manifest['driver_response_checks'],'driver')
        payload=pointer(driver,manifest['driver_payload_pointer']);used='driver';chosen=driver
    base=dict(schema='xar.r06.a32.frontier.file-result.v1',machine_id=manifest['machine_id'],
              evidence_kind=manifest['evidence_kind'],recorded_at_utc=datetime.now(timezone.utc).isoformat(),
              analysis_machine_id=analysis_machine,source_observed_at=manifest.get('source_observed_at'),
              source_machine_matches_analysis=analysis_machine==manifest['machine_id'],
              used_family_source=used,input_reads=list(READS),identity=values,
              request={'tool':tool,'arguments':arguments},scene_context=manifest.get('scene_context'),
              scene_context_scope='Root supplied context only; no R176/R186/R189 position transfer',
              SDK_calls=0,EXE_or_DLL_reads=0,builds=0,new_live_observation=False,
              provider_execution=False,current_variable_table_observed=False,native_receiver_selected=False,
              native_policy_caps={'reads':4096,'bytes':65536,'cooperative_deadline_ms':20,'total_prefix_limit':12},
              actual_total_reads=None,actual_total_bytes=None,actual_elapsed_ms=None,
              actual_budget_totals_exported=False,
              independent_internal_after_snapshot_read=False,
              same_frame_enforcement='Production GUI Driver/coordinator before/after native/public binding, independently compared here to Root supplied actual expected frame; no after snapshot reconstructed')
    if not complete_family(payload):
        return {**base,'status':'GUI_FAMILY_NOT_PUBLISHED_OR_INCOMPLETE','frontier_rows':[],
                'meaning':'This input cannot qualify a GUI source segment; absence is not an empty provider set.'}
    if tool=='ck3_execute_step':
        opener=pointer(chosen,manifest['opener_result_pointers'][used])
        require(type(opener) is dict and opener.get('status')=='verified_visible'
                and opener.get('postcondition_verified') is True and opener.get('verification_pending') is False,
                'opener did not verify a later visible military root')
        require(opener.get('later_military_tree') is payload,'selected family is not the actual opener returned later_military_tree')
        require(type(opener.get('queried_revision')) is int and opener['queried_revision']==arguments['expected_revision']==public['revision'],
                'opener request/public revision differs')
        require(opener.get('episode_run_id')==public['episode_run_id'],'opener episode differs')
        base['opener_postcondition_verified']=True
    source,normalize,normalize_frame=load_consumers(repo,manifest['consumer_files'])
    require(payload['callback_binding_source_12004']==source,'receiver source profile differs')
    frame=normalize_frame(payload['refill_receiver_frame_12004'])
    for key,value in expected.items():require(type(frame[key]) is type(value) and frame[key]==value,'GUI frame differs: '+key)
    observed_public=payload['refill_receiver_public_binding_12004']
    require(type(observed_public) is dict and observed_public.keys()==public.keys()
            and all(type(observed_public[k]) is type(v) and observed_public[k]==v for k,v in public.items()),'GUI public binding differs')
    clean=normalize(payload,{'widgets':[dict(w) for w in payload['widgets']]})
    candidates=[]
    for index,widget in enumerate(clean['widgets']):
        for callback in widget['standard_click_binding_12004']['callbacks']:
            expression=callback.get('indirect_target_3aa30e0',{}).get('expression_3a9f960',{})
            full=expression.get('receiver_entry_candidates_12004')
            if full is None:continue
            tail=full.get(CHILD)
            absent_reason=None
            if tail is None:
                absent_reason=('full_reader_returned_before_frontier8' if full['status']=='available' else
                    'not_published_after_depth8_failure' if full['unavailable_reason']=='candidate_parent_depth_exhausted' else
                    'frontier_not_reached_or_not_published')
            candidates.append(dict(widget_index=index,child_path=widget.get('child_path'),
                effective_visible=widget.get('effective_visible'),enabled=widget.get('enabled'),callback_index=callback['index'],
                full_status=full['status'],full_unavailable_reason=full['unavailable_reason'],
                original_failure=full.get('failure_diagnostic'),
                prefix=full.get('definition_chain_prefix_depth8'),
                continuation_status='absent' if tail is None else tail['status'],continuation_absent_reason=absent_reason,continuation=tail))
    require(len(candidates)<=4,'fixed tree source capture cap exceeded')
    rvas=sorted({e['provider_slot2_rva'] for item in candidates if item['continuation_status']=='available'
                 for row in item['continuation']['rows'] for e in row['entries'] if e['provider_slot2_rva'] is not None})
    return {**base,'status':'GUI_FAMILY_STRICTLY_CONSUMED','frame':frame,'public_binding':public,
            'root_available':payload.get('root_available'),'truncated':payload.get('truncated'),
            'candidates':candidates,'new_continuation_leaf_count':sum(c['continuation_status']!='absent' for c in candidates),
            'eligible_source_provider_slot2_rvas':rvas,'eligible_source_provider_slot2_rvas_hex':[f'0x{x:X}' for x in rvas],
            'meaning':'Only available bounded source segments are qualified. Provider RVA is a static research entry, not execution permission or a selected receiver.'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--repo-root',type=Path,default=REPO);parser.add_argument('--max-input-bytes',type=int,default=64*1024*1024)
    args=parser.parse_args();sys.dont_write_bytecode=True
    manifest_bytes=args.manifest.read_bytes();manifest=json.loads(manifest_bytes,object_pairs_hook=unique)
    result=extract(manifest,args.repo_root,args.max_input_bytes)
    result['manifest_pin']=dict(path=args.manifest.as_posix(),bytes=len(manifest_bytes),sha256=hashlib.sha256(manifest_bytes).hexdigest())
    result['extractor_pin']=dict(path=Path(__file__).as_posix(),sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    raw=(json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    require(len(raw)<=1024*1024,'selected metadata exceeds1MiB')
    with args.output.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
    print(json.dumps(dict(output=args.output.as_posix(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),status=result['status'],SDK_calls=0,new_live_observation=False)))

if __name__=='__main__':main()
