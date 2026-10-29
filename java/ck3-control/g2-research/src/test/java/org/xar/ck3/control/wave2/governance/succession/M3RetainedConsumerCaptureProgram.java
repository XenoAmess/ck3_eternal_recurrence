package org.xar.ck3.control.wave2.governance.succession;

/** Source for the shared qualified capture controller; this class starts no process. */
public final class M3RetainedConsumerCaptureProgram {
    private M3RetainedConsumerCaptureProgram() { }
    public static String pythonProgram() { return PROGRAM; }
    private static final String PROGRAM = """
        import copy,datetime,hashlib,json,subprocess,sys,tempfile
        from pathlib import Path
        root=Path(sys.argv[1]).resolve(strict=True)
        scratch=Path(sys.argv[2]).resolve(strict=True)
        relatives=[
            'ck3_autonomous_player/src/xar_autoplayer/bridge/service.py',
            'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py',
            'ck3_autonomous_player/src/xar_autoplayer/bridge/campaign_root_context_contract.py',
            'ck3_autonomous_player/src/xar_autoplayer/bridge/turn_bundle_contract.py',
            'ck3_autonomous_player/src/xar_autoplayer/bridge/succession_transition_contract.py',
            'ck3_autonomous_player/src/xar_autoplayer/bridge/succession_expectation_invalidation_v1.py',
            'ck3_autonomous_player/src/xar_autoplayer/bridge/succession_warm_publication_refresh_v1.py',
            'ck3_autonomous_player/tests/unit/test_r76_initial_succession_root_reuse.py',
            'ck3_autonomous_player/tests/unit/test_nonwar_planning_root_reuse.py',
            'ck3_autonomous_player/tests/unit/test_private_council_formal_consumer_v1.py',
            'ck3_autonomous_player/tests/unit/test_council_assign_councillor_action_v1.py',
            'ck3_autonomous_player/mod_bridge/tools/__init__.py',
            'ck3_autonomous_player/mod_bridge/tools/frame_parser.py',
            'ck3_autonomous_player/tests/fixtures/private_council_formal12002_actual.json',
            'ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_current_betrothal_negative.json',
            'tools/ck3_live_run_id.py']
        # Every repository source that can be imported is pinned before any repository import.
        paths={path.resolve() for package in (root/'ck3_autonomous_player/src',root/'tools/g2_saved_campaign') for path in package.rglob('*.py')}
        paths.update((root/relative).resolve(strict=True) for relative in relatives)
        def refs():
            out=[]
            for path in sorted(paths):
                raw=path.read_bytes();out.append({'path':path.relative_to(root).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
            return out
        before=refs();cases=[];rejected=[]
        sys.path[:0]=[str(root/'ck3_autonomous_player/tests/unit'),str(root/'ck3_autonomous_player/src'),str(root)]
        from test_r76_initial_succession_root_reuse import _InitialExpectationDriver
        from xar_autoplayer.bridge.service import GameplayBridgeService
        from xar_autoplayer.bridge.campaign_root_context_contract import QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP as STEP
        from xar_autoplayer.bridge.turn_bundle_contract import build_turn_bundle_v1
        from xar_autoplayer.bridge.succession_expectation_invalidation_v1 import invalidate_succession_state_from_root_v1 as invalidate
        from xar_autoplayer.bridge.succession_warm_publication_refresh_v1 import same_pid_hot_publication_refresh_v1 as warm
        schema='xar.java-succession-retained-consumer/v1'
        def request(operation,state,snapshot,material,restore_kind=None):
            bundle=build_turn_bundle_v1(snapshot,material)
            value={'schema':schema,'operation':operation,'state':copy.deepcopy(state),'snapshot':copy.deepcopy(snapshot),
                'campaign_root_result':copy.deepcopy(material),'turn_bundle':bundle}
            if operation=='warm_refresh':value['restore_kind']=restore_kind
            return value
        def execute(value):
            if value['operation']=='invalidate':return invalidate(value['state'],snapshot=value['snapshot'],campaign_root_result=value['campaign_root_result'])
            return warm(value['state'],snapshot=value['snapshot'],campaign_root_result=value['campaign_root_result'],restore_kind=value['restore_kind'])
        def capture(name,value,negative=False):
            original=copy.deepcopy(value)
            try:result=execute(value)
            except (ValueError,TypeError,KeyError) as error:
                if not negative:raise
                rejected.append({'name':name,'request':original,'error_type':type(error).__name__,'error_message':str(error)})
            else:
                if negative:raise RuntimeError('original unexpectedly accepted negative '+name)
                cases.append({'name':name,'request':original,'expected':copy.deepcopy(result)})
            if value!=original:raise RuntimeError('original consumer mutated caller input')
        with tempfile.TemporaryDirectory(prefix='m3-retained-consumer-',dir=scratch) as directory:
            driver=_InitialExpectationDriver(Path(directory))
            driver.frame.pop('succession_expectation',None)
            service=GameplayBridgeService(driver)
            prepared=service._prepare_succession_transition_v1(driver.take_snapshot(),{STEP})
            snapshot=driver.take_internal_semantic_snapshot()
            if snapshot['succession_expectation']!=prepared['succession_expectation']:raise RuntimeError('actual Service retention not observed')
            material=service.query_campaign_root_context_v1(expected_revision=snapshot['revision'])
            state={'expectation':copy.deepcopy(snapshot['succession_expectation']),'reconciliation':{'opaque_previous_projection':True},'opaque_extension':{'keep':[]}}
            base=request('invalidate',state,snapshot,material)
            capture('current_complete_root_keeps_retained_estate',copy.deepcopy(base))
            changed=copy.deepcopy(material)
            next(row for row in changed['campaign_root_context']['held_title_partition'] if not row['primary'])['first_heir_character_id']=99991
            if 'held_title_partition' in changed:changed['held_title_partition']=copy.deepcopy(changed['campaign_root_context']['held_title_partition'])
            changed['query_sequence']+=1
            capture('same_publication_full_root_changed_estate',request('invalidate',state,snapshot,changed))
            capture('missing_expectation_preserves_original_state',request('invalidate',{'opaque_extension':[]},snapshot,material))
            for name,change in [('mixed_root_frame',lambda v:v['campaign_root_result']['binding'].update(native_revision=v['snapshot']['native_revision']+1)),
                    ('terminal_snapshot',lambda v:v['snapshot'].update(one_life_terminal=True)),
                    ('different_episode',lambda v:v['snapshot'].update(episode_run_id='different-episode'))]:
                value=copy.deepcopy(base);change(value);capture(name,value,True)
            # A real fresh Service query in a new SDK publication domain. Only fixture Native data is synthetic.
            driver.frame.update(snapshot_id='native:60',revision=61,native_revision=60)
            driver.frame.pop('succession_expectation',None)
            service._prepare_succession_transition_v1(driver.take_snapshot(),{STEP})
            old={'expectation':copy.deepcopy(driver.frame['succession_expectation']),'reconciliation':{'opaque_previous_projection':True}}
            driver.frame.update(snapshot_id='native:61',revision=2,native_revision=61)
            current=driver.take_internal_semantic_snapshot()
            fresh=service.query_campaign_root_context_v1(expected_revision=2)
            warm_base=request('warm_refresh',old,current,fresh,'same_pid_hot')
            capture('fresh_warm_root_refreshes_sdk_publication_domain',copy.deepcopy(warm_base))
            other=copy.deepcopy(warm_base);other['restore_kind']='cold_checkpoint';capture('cold_kind_does_not_grant_warm_refresh',other)
            equal=copy.deepcopy(warm_base);equal['snapshot']['revision']=61;capture('nonreset_publication_keeps_original_guard',equal)
            for name,change in [('warm_actor_changed',lambda v:v['snapshot']['played_character'].update(character_id=99990)),
                    ('warm_native_backwards',lambda v:v['snapshot'].update(native_revision=59)),
                    ('warm_partial_root',lambda v:v['campaign_root_result']['campaign_root_context']['readiness'].update(held_title_partition_ready=False)),
                    ('warm_root_frame_changed',lambda v:v['campaign_root_result']['binding'].update(native_revision=62))]:
                value=copy.deepcopy(warm_base);change(value);capture(name,value,True)
            if driver.requests or driver.submit_calls:raise RuntimeError('capture submitted a Native command')
            observations={'service_complete_root_calls':driver.root_calls,'retained_bundles':len(driver.retained_bundles),'gameplay_submissions':0}
        runtime_dependencies=(root/'tools/.venv').resolve()
        imported={Path(module.__file__).resolve() for module in list(sys.modules.values())
            if getattr(module,'__file__',None) and str(module.__file__).endswith('.py') and Path(module.__file__).resolve().is_relative_to(root)
            and not Path(module.__file__).resolve().is_relative_to(runtime_dependencies)}
        if not imported<=paths:raise RuntimeError('repository import outside pre-import source pins: '+repr(sorted(str(path) for path in imported-paths)))
        after=refs()
        if before!=after:raise RuntimeError('original listed consumer sources changed')
        machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
        output=json.dumps({'schema':'xar.g2.m3.original-retained-consumer-golden/v1','machine_id':machine,
            'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),'synthetic_fixture':True,
            'source_refs':before,'source_refs_unchanged':True,'actual_repository_import_count':len(imported),
            'runtime_dependency_root_excluded_from_project_source_pins':str(runtime_dependencies),'python_executable':sys.executable,'python_version':sys.version,
            'source_pin_scope':'All source packages and exact fixture/test leaves pinned before repository imports; actual import subset and full source postcheck required',
            'observations':observations,'cases':cases,'rejected':rejected,
            'scope':'Actual Service root materialization and complete turn bundle passed to unchanged original invalidation/warm functions. Synthetic memory backend only; no campaign Driver/SAVE body, game, native pipe, writer or continuation.'},ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')
        if len(output)>2097152:raise RuntimeError('consumer capture output '+str(len(output))+' bytes exceeds admitted 2 MiB estimate')
        sys.stdout.buffer.write(output+b'\\n')
        """;
}
