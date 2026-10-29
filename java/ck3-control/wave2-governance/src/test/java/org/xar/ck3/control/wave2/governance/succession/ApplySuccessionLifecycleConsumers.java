package org.xar.ck3.control.wave2.governance.succession;

/** Original consumer suites for Root's one already-bootstrapped Python/Java session. */
public final class ApplySuccessionLifecycleConsumers {
    private ApplySuccessionLifecycleConsumers() { }
    /** Execute once in Root's session, then call the typed run_succession_lifecycle_consumer_application_v1 function. The returned status is mandatory. */
    public static String pythonConsumerHarness() { return SCRIPT; }
    private static final String SCRIPT = """
    import os,tempfile,sys,json,hashlib,datetime,importlib,importlib.util,importlib.abc,inspect,copy,contextlib
    from pathlib import Path
    from collections import Counter
    from tools.g2_saved_campaign.current_saved_basis_v1 import ExactRefV1
    
    def run_succession_lifecycle_consumer_application_v1(*,root:Path,candidate:Path,scratch:Path,canonical_test_repository:Path,succession_golden_ref:ExactRefV1,lifecycle_golden_ref:ExactRefV1)->dict[str,object]:
        root,candidate,scratch,canonical_test_repository=[Path(path).resolve(strict=True) for path in (root,candidate,scratch,canonical_test_repository)]
        if not isinstance(succession_golden_ref,ExactRefV1) or not isinstance(lifecycle_golden_ref,ExactRefV1):raise ValueError('typed exact original golden refs required')
        succession_path,succession_sha=succession_golden_ref.path,succession_golden_ref.sha256
        lifecycle_path,lifecycle_sha=lifecycle_golden_ref.path,lifecycle_golden_ref.sha256
        if os.environ.get('XAR_REPO_ROOT') is None or Path(os.environ['XAR_REPO_ROOT']).resolve()!=root:raise ValueError('Root must set XAR_REPO_ROOT before fixture imports')
        if not sys.dont_write_bytecode:raise ValueError('Root must disable bytecode before bootstrap')
        if Path(tempfile.gettempdir()).resolve()!=scratch:raise ValueError('Root must configure TEMP/TMP/TMPDIR and tempfile before bootstrap to the approved scratch')
        previous_profile=sys.getprofile()
        report={'schema':'xar.java-succession-lifecycle-consumer-application/v1','status':'RED','machine_id':'unknown','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Existing Java host results applied through original Driver/Service and pure WAL/readonly-prefix/invalidation/warm/rebinder fixture consumers. No Game, native endpoint, SDK continuation or live recovery authority. Operating context is compatibility-only and excluded from the seven registered projection operations.','Python_business_fallback':False}
        pinned={}
        def pin(path,expected=None):
            path=Path(path).resolve(strict=True);raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
            if expected is not None and (type(expected) is not str or digest!=expected):raise ValueError('source/input SHA mismatch: '+str(path))
            row={'path':str(path),'bytes':len(raw),'sha256':digest}
            pinned[str(path)]=row
            return row
        def unchanged():
            for row in list(pinned.values()):
                path=Path(row['path']);raw=path.read_bytes()
                if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('input/source changed during application: '+str(path))
        def same(actual,expected):
            if json.dumps(actual,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)!=json.dumps(expected,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False):raise AssertionError('actual Java/consumer result differs from original JSON oracle')
        def main():
            sys.path[:0]=[str(root),str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit')]
            producer='xar_autoplayer.bridge.succession_transition_contract'
            reader_names=['checkpoint_environment_rebinder','ordinary_seed_rebinder','rogue_checkpoint_rebinder','cold_checkpoint_validator']
            overlays={producer:candidate/'ck3_autonomous_player/src/xar_autoplayer/bridge/succession_transition_contract.py'}
            overlays.update({'xar_autoplayer.'+name:candidate/'ck3_autonomous_player/src/xar_autoplayer'/str(name+'.py') for name in reader_names})
            client_name='tools.g2_saved_campaign.java_map_admission_client_v1'
            client=importlib.import_module(client_name)
            config=client.require_current_projection_config_v1()
            if config.transport is not None:raise ValueError('actual Root shared session may not use injected transport')
            client_path=Path(config.client_source_ref.path).resolve(strict=True);client_sha=config.client_source_ref.sha256
            if Path(client.__file__).resolve()!=client_path:raise ValueError('Root common client module source differs from actual config')
            pin(client_path,client_sha)
            for name,path in overlays.items():
                loaded=sys.modules.get(name)
                if loaded is not None and Path(loaded.__file__).resolve()!=path.resolve():raise RuntimeError('Root must install the candidate import graph before bootstrap/Driver imports: '+name)
                pin(path)
            class Overlay(importlib.abc.MetaPathFinder):
                def find_spec(self,fullname,path=None,target=None):
                    source=overlays.get(fullname)
                    return None if source is None else importlib.util.spec_from_file_location(fullname,source)
            sys.meta_path.insert(0,Overlay())
            identity=client.qualify_projection_service_v1(config)
            report['machine_id']=config.machine_id
            report['service_evidence_ref']=config.service.service_evidence_ref.to_wire()
            report['program_ref']=config.service.program_ref.to_wire()
            report['host_identity_sha256']=identity.identity_sha256
            report['shared_client_ref']=pin(client_path,client_sha)
            report['consumer_graph_root']=str(root)
            report['canonical_test_repository']=str(canonical_test_repository)
            observed=Counter();route_evidence={};observer_errors=[]
            required=['bridge/native_driver.py','bridge/service.py','bridge/succession_binding_refresh_wal_v1.py','bridge/succession_expectation_invalidation_v1.py','bridge/succession_warm_publication_refresh_v1.py','tools/g2_saved_campaign/current_saved_basis_v1.py']+[name+'.py' for name in reader_names]
            def observer(frame,event,result):
                if previous_profile is not None:previous_profile(frame,event,result)
                if event!='return' or frame.f_code is not client.call_projection_v1.__code__ or not isinstance(result,client.ProjectionResult):return
                try:
                    client.require_result_context_v1(result,config=config,operation=result.operation,request_id=result.request_id,payload=frame.f_locals['payload'])
                    if not result.http_call.actual_http_invoked or result.http_call.transport_kind!='stdlib-http-loopback/v1':raise ValueError('actual Java HTTP custody required')
                    outer=frame.f_back;found=set()
                    while outer is not None:
                        source=Path(outer.f_code.co_filename).as_posix()
                        for suffix in required:
                            if source.endswith('/'+suffix):found.add(suffix)
                        outer=outer.f_back
                    for suffix in found:
                        observed[(suffix,result.operation.value)]+=1
                        if suffix not in route_evidence:
                            route_evidence[suffix]={'request_id':result.request_id,'operation':result.operation.value,'payload_sha256':result.payload_sha256,'response_sha256':result.response_sha256,'result_sha256':hashlib.sha256(result.result_bytes).hexdigest(),'http_status':result.http_call.http_status,'actual_http_invoked':result.http_call.actual_http_invoked,'http_call_sha256':hashlib.sha256(json.dumps(result.http_call.to_wire(),sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest(),'process_before':result.http_call.process_before.to_wire(),'process_after':result.http_call.process_after.to_wire()}
                except Exception as error:
                    observer_errors.append(type(error).__name__+': '+str(error))
            sys.setprofile(observer)
            contract=importlib.import_module(producer)
            readers={name:importlib.import_module('xar_autoplayer.'+name) for name in reader_names}
            for name,path in overlays.items():
                if Path(importlib.import_module(name).__file__).resolve()!=path.resolve():raise RuntimeError('candidate import origin differs: '+name)
            from xar_autoplayer.bridge import native_driver
            for name in ('freeze_succession_expectation_v1','normalize_succession_expectation_v1','reconcile_succession_transition_v1'):
                if Path(inspect.getsourcefile(getattr(native_driver,name))).resolve()!=overlays[producer].resolve():raise RuntimeError('original Driver retained an old Python policy alias')
            def golden(path,digest,schema):
                pin(path,digest);value=client.decode_projection_object_v1(Path(path).read_bytes(),maximum_bytes=131072)
                if value.get('schema')!=schema or value.get('source_refs_unchanged') is not True:raise ValueError('actual original golden schema/source closure required')
                refs=value.get('source_refs')
                if type(refs) is not list or not refs:raise ValueError('actual original source refs missing')
                for row in refs:
                    relative=Path(row['path'])
                    if relative.is_absolute() or '..' in relative.parts:raise ValueError('original source ref escapes repository')
                    observed_ref=pin(canonical_test_repository/relative,row['sha256'])
                    if observed_ref['bytes']!=row['bytes']:raise ValueError('original source byte count differs')
                return value
            if Path(succession_path).stat().st_size!=succession_golden_ref.bytes or Path(lifecycle_path).stat().st_size!=lifecycle_golden_ref.bytes:raise ValueError('actual original golden byte count differs from typed refs')
            succession=golden(succession_path,succession_sha,'xar.java-succession-original-producer-golden/v1')
            lifecycle=golden(lifecycle_path,lifecycle_sha,'xar.java-succession-lifecycle-original-golden/v1')
            for source,minimum in [(succession,15),(lifecycle,24)]:
                original=source.get('original_unittest')
                if type(original) is not dict or original.get('whole_module',original.get('whole_modules')) is not True or type(original.get('tests')) is not int or original['tests']<minimum or original['tests']!=original.get('discovered_tests') or len(original.get('discovered_test_ids',[]))!=original['tests'] or any(original.get(key)!=0 for key in ('failures','errors','skipped')):raise ValueError('full original suite discovery/pass evidence is mandatory')
            if len(succession.get('cases',[]))!=18 or len(lifecycle.get('cases',[]))!=8 or len(lifecycle.get('rejections',[]))!=16 or len(lifecycle.get('anchor_consumer_cases',[]))!=20:raise ValueError('mandatory original cases are missing; no subset admission')
            projected=0
            for case in succession['cases']+succession['actual_driver_consumer_requests']+succession['actual_root_consumer_requests']:
                request=copy.deepcopy(case['request']);op=request['operation']
                if op=='operating':continue
                if op=='freeze':actual=contract.freeze_succession_expectation_v1(request['turn_bundle'],episode_run_id=request['episode_run_id'],episode_character_id=request['episode_character_id'])
                elif op=='normalize':actual=contract.normalize_succession_expectation_v1(request['expectation'])
                elif op=='reconcile':actual=contract.reconcile_succession_transition_v1(request['expectation'],request['post_snapshot'],request['post_turn_bundle'])
                else:raise ValueError('unknown original golden operation')
                same(actual,case['expected']);projected+=1
                if op in ('freeze','normalize') and case.get('actual_consumers') is not None:
                    from xar_autoplayer.bridge.succession_binding_refresh_wal_v1 import _expectation
                    from tools.g2_saved_campaign.current_saved_basis_v1 import parse_readonly_prefix_driver_flags_v1
                    def consumed(function,value):
                        try:return {'accepted':True,'output':function(copy.deepcopy(value))}
                        except ValueError:return {'accepted':False,'output':None}
                    same(consumed(_expectation,{'succession_expectation':actual}),case['actual_consumers']['binding_refresh_wal'])
                    flags={'managed_restore_transaction':None,'rollback_war_failure':None,'succession_expectation':actual,'rollback_war_failures':[],'session_binding_present':False}
                    same(consumed(lambda value:parse_readonly_prefix_driver_flags_v1(value).to_wire(),flags),case['actual_consumers']['readonly_prefix_driver_flags'])
            from xar_autoplayer.errors import AgentError
            def outcome(function,*args):
                try:return {'accepted':True,'binding':function(*copy.deepcopy(args))}
                except (ValueError,AgentError):return {'accepted':False,'binding':None}
            def state(anchors):
                return {'format_version':2,'succession_lifecycle':anchors[0],'last_checkpoint':{'history_index':1,'succession_lifecycle':anchors[1]},'command_history':[{'index':1,'command':'save-checkpoint','ok':True,'result':{'checkpoint':{'succession_lifecycle':anchors[2]}}}]}
            for case in lifecycle['cases']:
                request=case['request'];op=request['operation']
                actual=contract.legacy_rogue_one_life_binding_v1() if op=='legacy' else contract.unknown_succession_lifecycle_binding_v1() if op=='unknown' else contract.normalize_succession_lifecycle_binding_v1(request['binding'])
                same(actual,case['expected'])
                for name,function in [('ordinary_seed_binding',readers['ordinary_seed_rebinder']._ordinary_binding),('rogue_checkpoint_binding',readers['rogue_checkpoint_rebinder']._rogue_binding)]:
                    same(outcome(function,actual,'actual Java application'),case['actual_consumers'][name])
            rejected_count=0
            for case in lifecycle['rejections']:
                value=client.decode_projection_json_v1(case['raw_binding_json'].encode('utf-8'),maximum_bytes=16384)
                try:contract.normalize_succession_lifecycle_binding_v1(value)
                except client.ProjectionDomainRejected as error:
                    if not error.http_call.actual_http_invoked or error.http_call.transport_kind!='stdlib-http-loopback/v1':raise AssertionError('original negative case lacked actual Java rejection evidence')
                    rejected_count+=1
                else:raise AssertionError('actual Java accepted original lifecycle negative case')
            for case in lifecycle['anchor_consumer_cases']:
                value=state(copy.deepcopy(case['anchors']))
                for key,function in [('checkpoint_environment_binding',readers['checkpoint_environment_rebinder']._checkpoint_binding),('ordinary_seed_anchors',lambda value:readers['ordinary_seed_rebinder']._source_lifecycle_anchors(value)[-1]),('rogue_checkpoint_anchors',lambda value:readers['rogue_checkpoint_rebinder']._source_lifecycle_anchors(value)[-1])]:
                    same(outcome(function,value),case['actual_consumers'][key])
            names=['test_succession_transition_contract','test_ordinary_succession_operating_context_v1','test_succession_binding_refresh_wal_v1','test_succession_expectation_invalidation_v1','test_succession_warm_publication_refresh_v1','test_succession_expectation_freshness_v1','test_r76_initial_succession_root_reuse','test_verified_vanilla_succession','test_checkpoint_environment_rebinder','test_ordinary_seed_rebinder','test_rogue_checkpoint_rebinder','test_cold_checkpoint_type_contract']
            suites=[root/'ck3_autonomous_player/tests/unit'/str(name+'.py') for name in names]
            for path in suites:pin(path)
            for path in ['ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/src/xar_autoplayer/bridge/succession_binding_refresh_wal_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/succession_expectation_invalidation_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/succession_warm_publication_refresh_v1.py','tools/g2_saved_campaign/current_saved_basis_v1.py','ck3_autonomous_player/tests/fixtures/private_council_formal12002_actual.json','ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_current_betrothal_negative.json','docs/ck3-native-ai/evidence/p50r1-natural-successor-actual-2026-10-18.json']:pin(root/path)
            wal_scratch=scratch/'wal';wal_scratch.mkdir(exist_ok=False)
            wal_test=importlib.import_module('test_succession_binding_refresh_wal_v1');wal_test.configure_scratch(wal_scratch)
            class Results:
                def __init__(self):self.collected=Counter();self.passed=0;self.failed=0;self.skipped=0;self.errors=0
                def pytest_collection_modifyitems(self,session,config,items):
                    for item in items:self.collected[str(Path(item.path).resolve())]+=1
                def pytest_runtest_logreport(self,report):
                    if report.skipped:self.skipped+=1
                    if report.failed:
                        if report.when=='call':self.failed+=1
                        else:self.errors+=1
                    if report.when=='call' and report.passed:self.passed+=1
                def pytest_collectreport(self,report):
                    if report.failed:self.errors+=1
            import pytest
            results=Results()
            exitcode=pytest.main(['-q','--tb=line','-p','no:cacheprovider','-p','no:faulthandler','--basetemp',str(scratch/'pytest'),*map(str,suites)],plugins=[results])
            sys.setprofile(previous_profile)
            missing_suites=[str(path) for path in suites if results.collected[str(path.resolve())]==0]
            missing_routes=[name for name in required if name not in route_evidence]
            unchanged()
            report.update({'original_suite_exit':int(exitcode),'original_suites':[{'source':str(path),'collected':results.collected[str(path.resolve())]} for path in suites],'passed':results.passed,'failed':results.failed,'errors':results.errors,'skipped':results.skipped,'missing_suites':missing_suites,'missing_actual_consumer_routes':missing_routes,'observer_errors':observer_errors[:5],'original_golden_projected_cases':projected,'actual_Java_lifecycle_rejections':rejected_count,'actual_consumer_call_counts':[{'source':source,'operation':operation,'count':count} for (source,operation),count in sorted(observed.items())],'first_actual_call_per_consumer':route_evidence,'source_refs':list(pinned.values()),'source_refs_unchanged':True,'WAL_scratch_peak_bound':wal_test.PEAK_BOUND,'WAL_actual_write_count':wal_test.WRITE_COUNT})
            if exitcode or results.failed or results.errors or results.skipped or missing_suites or missing_routes or observer_errors or results.passed==0:raise AssertionError('full original consumer suite/application is RED; see exact counters and missing routes')
            report['status']='PASS'
        try:
            with contextlib.redirect_stdout(sys.stderr):main()
        except Exception as error:
            report['error']=type(error).__name__+': '+str(error)
        finally:
            sys.setprofile(previous_profile)
        return report
    """;
}

