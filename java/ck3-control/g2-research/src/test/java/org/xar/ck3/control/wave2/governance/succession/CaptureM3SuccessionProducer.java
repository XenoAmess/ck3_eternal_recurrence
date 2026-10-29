package org.xar.ck3.control.wave2.governance.succession;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.LinkOption;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Bounded original-code oracle, run only inside the released managed execution scope.
 * Backend material, in-memory Driver owner and persistence callback are explicitly synthetic.
 * This never opens a campaign Driver/SAVE, a native pipe, a Game or a writer. */
public final class CaptureM3SuccessionProducer {
    private CaptureM3SuccessionProducer() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length == 2 && arguments[0].equals("export-retained-consumer-program")) {
            exportRetainedConsumerProgram(Path.of(arguments[1]));
            return;
        }
        if (arguments.length != 6 || !arguments[4].matches("[1-9][0-9]*") || !arguments[5].matches("[0-9a-f]{64}")) {
            throw new IllegalArgumentException("repository-root existing-python new-output-json compatibility-test-path exact-test-bytes test-sha256");
        }
        Fixture fixture = new Fixture(Path.of(arguments[3]), Long.parseLong(arguments[4]), arguments[5]);
        requireExactFixture(fixture);
        Path root = Path.of(arguments[0]).toRealPath();
        Path output = Path.of(arguments[2]).toAbsolutePath().normalize();
        if (Files.exists(output) || !Files.isDirectory(output.getParent())) {
            throw new IllegalArgumentException("existing owned output parent and create-only capture required");
        }
        Path scratch = Files.createTempDirectory(output.getParent(), "m3-original-fixtures-");
        ProcessBuilder builder = new ProcessBuilder(List.of(arguments[1], "-B", "-c", SCRIPT, root.toString(), scratch.toString(), fixture.path().toString()));
        builder.directory(root.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT);
        builder.environment().keySet().removeIf(key -> List.of("PYTHONHOME", "PYTHONPATH", "PYTHONUSERBASE", "PYTHONPYCACHEPREFIX", "PYTHONSAFEPATH", "PYTHONUTF8",
                "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS").contains(key.toUpperCase(java.util.Locale.ROOT)));
        builder.environment().put("PYTHONNOUSERSITE", "1");
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONSAFEPATH", "1");
        builder.environment().put("PYTHONPYCACHEPREFIX", scratch.resolve("absent-bytecode-cache").toString());
        builder.environment().put("PYTHONUTF8", "1");
        builder.environment().put("OPENBLAS_NUM_THREADS", "1");
        builder.environment().put("OMP_NUM_THREADS", "1");
        builder.environment().put("MKL_NUM_THREADS", "1");
        builder.environment().put("NUMEXPR_NUM_THREADS", "1");
        Process process = builder.start();
        byte[] bytes;
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var read = executor.submit(() -> process.getInputStream().readNBytes(786_433));
            if (!process.waitFor(120, TimeUnit.SECONDS)) {
                process.descendants().forEach(ProcessHandle::destroyForcibly);
                process.destroyForcibly();
                throw new IllegalStateException("original M3 capture timed out");
            }
            bytes = read.get(10, TimeUnit.SECONDS);
        } finally {
            if (process.isAlive()) { process.destroyForcibly(); }
        }
        if (process.exitValue() != 0 || bytes.length == 0 || bytes.length > 786_432) {
            throw new IllegalStateException("original M3 producer capture failed: exit=" + process.exitValue() + ", bytes=" + bytes.length);
        }
        requireExactFixture(fixture);
        Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
        System.out.println("Actual original M3 capture bytes=" + bytes.length + "; output=" + output);
    }

    /** Fixed, mechanical extraction only; the qualified shared controller owns execution. */
    private static void exportRetainedConsumerProgram(Path requestedOutput) throws Exception {
        Path output = requestedOutput.toAbsolutePath().normalize();
        if (Files.exists(output, LinkOption.NOFOLLOW_LINKS) || output.getParent() == null
                || !Files.isDirectory(output.getParent()) || !output.getParent().toRealPath().equals(output.getParent())) {
            throw new IllegalArgumentException("existing owned real parent and create-only script output required");
        }
        Object value = Class.forName("org.xar.ck3.control.wave2.governance.succession.M3RetainedConsumerCaptureProgram")
                .getMethod("pythonProgram").invoke(null);
        if (!(value instanceof String program) || program.isEmpty()) {
            throw new IllegalArgumentException("fixed retained-consumer capture program required");
        }
        byte[] raw = program.getBytes(StandardCharsets.UTF_8);
        if (raw.length > 262_144) { throw new IllegalArgumentException("bounded retained-consumer script required"); }
        Files.write(output, raw, StandardOpenOption.CREATE_NEW);
        byte[] observed;
        try (var input = Files.newInputStream(output)) { observed = input.readNBytes(262_145); }
        if (!java.util.Arrays.equals(raw, observed) || Files.size(output) != raw.length) {
            throw new IllegalStateException("mechanical script export readback mismatch");
        }
        System.out.println("Mechanical retained-consumer script export bytes=" + raw.length + "; sha256="
                + HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(observed)) + "; output=" + output);
    }

    private record Fixture(Path path, long bytes, String sha256) {
        private Fixture {
            if (path == null || !path.isAbsolute() || !path.normalize().equals(path)
                    || !path.getFileName().toString().equals("test_r76_initial_succession_root_reuse.py")
                    || bytes <= 0 || bytes > 65_536 || sha256 == null || !sha256.matches("[0-9a-f]{64}")) {
                throw new IllegalArgumentException("bounded explicit compatibility test source required");
            }
        }
    }
    private static void requireExactFixture(Fixture fixture) throws Exception {
        if (!Files.isRegularFile(fixture.path(), LinkOption.NOFOLLOW_LINKS) || Files.isSymbolicLink(fixture.path())
                || !fixture.path().toRealPath().equals(fixture.path()) || Files.size(fixture.path()) != fixture.bytes()) {
            throw new IllegalArgumentException("exact compatibility fixture path/size required");
        }
        byte[] raw;
        try (var input = Files.newInputStream(fixture.path())) { raw = input.readNBytes(65_537); }
        if (raw.length != fixture.bytes() || Files.size(fixture.path()) != fixture.bytes()
                || !HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)).equals(fixture.sha256())) {
            throw new IllegalArgumentException("exact compatibility fixture SHA required");
        }
    }

    private static final String SCRIPT = """
            import sys,json,copy,hashlib,subprocess,datetime,threading,unittest
            from pathlib import Path
            root=Path(sys.argv[1]);scratch=Path(sys.argv[2]);compatibility_test=Path(sys.argv[3]).resolve()
            sys.path[:0]=[str(root/'ck3_autonomous_player/src'),str(root/'ck3_autonomous_player/tests/unit'),str(root/'tools'),str(root)]
            historical_path=root/'docs/ck3-native-ai/evidence/p50r1-natural-successor-actual-2026-10-18.json'
            # Pin the source-only import roots before execution, including lazily loaded leaves.
            # This enumerates Python source, never arbitrary runtime JSON or persistence.
            paths={path.resolve() for package in (root/'ck3_autonomous_player/src',root/'tools/g2_saved_campaign') for path in package.rglob('*.py')}
            paths.update((root/'ck3_autonomous_player/tests/unit'/name).resolve() for name in ('test_succession_transition_contract.py','test_r76_initial_succession_root_reuse.py','test_succession_expectation_freshness_v1.py','test_private_council_formal_consumer_v1.py','test_nonwar_planning_root_reuse.py'))
            paths.update((root/name).resolve() for name in ('ck3_autonomous_player/mod_bridge/tools/__init__.py','ck3_autonomous_player/mod_bridge/tools/frame_parser.py','ck3_autonomous_player/tests/unit/test_council_assign_councillor_action_v1.py'))
            paths.update([(root/'ck3_autonomous_player/tests/fixtures/private_council_formal12002_actual.json').resolve(),historical_path.resolve(),(root/'tools/ck3_live_run_id.py').resolve()])
            paths.add(compatibility_test)
            def refs():
                result=[]
                for path in sorted(paths):
                    raw=path.read_bytes();name=str(path.relative_to(root)).replace('\\\\','/') if path.is_relative_to(root) else str(path)
                    result.append({'path':name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
                return result
            before=refs()
            import pytest
            import test_succession_transition_contract as original_tests
            import importlib.util
            fixture_spec=importlib.util.spec_from_file_location('test_r76_initial_succession_root_reuse',compatibility_test)
            root_tests=importlib.util.module_from_spec(fixture_spec)
            sys.modules['test_r76_initial_succession_root_reuse']=root_tests
            fixture_spec.loader.exec_module(root_tests)
            import test_succession_expectation_freshness_v1 as freshness_tests
            from xar_autoplayer.bridge.service import GameplayBridgeService
            from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver,load_native_driver_state_for_resume_payload
            from xar_autoplayer.bridge.succession_transition_contract import freeze_succession_expectation_v1 as freeze,normalize_succession_expectation_v1 as normalize
            from xar_autoplayer.bridge.campaign_root_context_contract import QUERY_CAMPAIGN_ROOT_CONTEXT_V1_STEP as ROOT_STEP
            from xar_autoplayer.bridge.succession_binding_refresh_wal_v1 import _business
            from g2_saved_campaign.succession_expectation_freshness_v1 import observe_succession_expectation_freshness_v1 as freshness
            from g2_saved_campaign.current_saved_basis_v1 import parse_readonly_prefix_driver_flags_v1
            names=['test_freezes_exact_per_title_expectation','test_legacy_three_field_rows_remain_recovery_compatible','test_rejects_malformed_current_capital_province','test_reconciles_only_titles_owned_by_the_predecessor','test_reports_successor_and_title_mismatches_without_inventing_holders','test_freezes_no_heir_as_observed_risk','test_rejects_cross_frame_and_non_transition_inputs','test_persisted_expectation_normalizer_rejects_identity_drift']
            run=unittest.TextTestRunner(stream=sys.stderr).run(unittest.TestSuite(original_tests.SuccessionTransitionContractTests(name) for name in names))
            if not run.wasSuccessful() or run.testsRun!=8 or run.skipped:raise RuntimeError('original complete transition suite did not pass')
            def focused_call(call):
                try:return call()
                except AssertionError as error:
                    trace=error.__traceback__
                    while trace is not None:
                        local=trace.tb_frame.f_locals
                        if 'shared_material' in local and 'fresh_material' in local:
                            differences=[]
                            def diff(left,right,path=''):
                                if len(differences)>=64:return
                                if isinstance(left,dict) and isinstance(right,dict):
                                    for key in sorted(set(left)|set(right)):
                                        if key not in left or key not in right:differences.append({'path':path+'/'+key,'presence_left':key in left,'presence_right':key in right})
                                        else:diff(left[key],right[key],path+'/'+key)
                                elif isinstance(left,list) and isinstance(right,list):
                                    if len(left)!=len(right):differences.append({'path':path,'left_length':len(left),'right_length':len(right)})
                                    for index,(a,b) in enumerate(zip(left,right)):diff(a,b,path+'/'+str(index))
                                elif type(left) is not type(right) or left!=right:
                                    differences.append({'path':path,'left_type':type(left).__name__,'right_type':type(right).__name__,'left':repr(left)[:512],'right':repr(right)[:512]})
                            diff(local['shared_material'],local['fresh_material'])
                            print(json.dumps({'schema':'xar.g2.m3.original-test-material-diff/v1','function':trace.tb_frame.f_code.co_name,'case':local.get('case'),'differences':differences,'limit':64},ensure_ascii=True,separators=(',',':')),file=sys.stderr)
                        trace=trace.tb_next
                    raise
            focused=scratch/'focused';focused.mkdir()
            with pytest.MonkeyPatch.context() as patch:
                focused_call(lambda:root_tests.test_r76_initial_expectation_reuses_current_root_and_keeps_fresh_defaults(focused,patch))
            focused_fresh=scratch/'focused-freshness';focused_fresh.mkdir()
            with pytest.MonkeyPatch.context() as patch:
                focused_call(lambda:freshness_tests.test_ordinary_planner_refreshes_3121_day_estate_once_from_existing_full_root(focused_fresh,patch))
            freshness_tests.test_historical_old_projection_and_primary_heir_do_not_become_fresh_all_titles()
            producer_cases=[];producer_rejected=[];service_observations=[]
            freshness_cases=[];freshness_rejected=[];consumer_cases=[];consumer_rejected=[]
            def capture(cases,rejected,name,request,call,expect_error=False):
                preserved=copy.deepcopy(request)
                try:expected=call(copy.deepcopy(request))
                except (ValueError,RuntimeError,AssertionError) as error:
                    if not expect_error:raise
                    rejected.append({'name':name,'request':preserved,'error_type':type(error).__name__,'error_message':str(error)});return
                if expect_error:raise RuntimeError('original unexpectedly accepted negative '+name)
                cases.append({'name':name,'request':preserved,'expected':copy.deepcopy(expected)})
            class MemoryOwner:
                # This is the only synthetic persistence seam; original Driver methods run unchanged.
                allow_driver_state_wal_v1=False
                def __init__(self,snapshot,expectation=None):
                    self.snapshot=copy.deepcopy(snapshot);self._driver_state_lock=threading.RLock()
                    self._episode_character_id=snapshot.get('episode_character_id');self._episode_run_id=snapshot.get('episode_run_id')
                    self._succession_expectation=copy.deepcopy(expectation);self._succession_reconciliation=None;self.persist_calls=0
                def take_internal_semantic_snapshot(self):return copy.deepcopy(self.snapshot)
                def _persist_driver_state(self,**kwargs):
                    assert kwargs=={'persistence_reason':'succession_expectation'};self.persist_calls+=1
            def produce(request):
                owner=MemoryOwner(request['snapshot'],request.get('expectation'))
                if request['operation']=='retain':
                    result=NativeHeadlessGameplayDriver.retain_succession_expectation_v1(owner,request['turn_bundle'],expected_revision=request['expected_revision'])
                    assert owner.persist_calls==1 and owner._succession_expectation==result
                else:
                    result=NativeHeadlessGameplayDriver.reconcile_retained_succession_transition_v1(owner,request['turn_bundle'],expected_revision=request['expected_revision'])
                    assert owner.persist_calls==0 and owner._succession_reconciliation==result
                return result
            def request(operation,snapshot,bundle,expectation=None):
                value={'schema':'xar.java-succession-planning-producer/v1','operation':operation,'snapshot':copy.deepcopy(snapshot),'turn_bundle':copy.deepcopy(bundle),'expected_revision':snapshot['revision']}
                if operation=='reconcile':value['expectation']=copy.deepcopy(expectation)
                return value
            seeds=[]
            with pytest.MonkeyPatch.context() as patch:
                patch.setattr('xar_autoplayer.bridge.service.choose_one_life_turn',lambda *_a,**_k:{'policy':'one-life-turn-v1','phase':'offline_ordinary_advance','selected_step':'life-advance'})
                for mode in ('current_root','native_changed','date_changed','date_changes_before_bundle_snapshot','old_3121_days'):
                    state=scratch/('service-'+mode);state.mkdir();driver=root_tests._InitialExpectationDriver(state)
                    driver.frame.pop('succession_expectation',None)
                    def retain(bundle,*,expected_revision):
                        value=request('retain',driver.take_internal_semantic_snapshot(),bundle)
                        assert value['expected_revision']==expected_revision
                        result=produce(value)
                        capture(producer_cases,producer_rejected,'service_'+mode+'_retain_'+str(len(driver.retained_bundles)),value,produce)
                        driver.frame['succession_expectation']=copy.deepcopy(result);driver.retained_bundles.append(copy.deepcopy(bundle));seeds.append(copy.deepcopy(result))
                    driver.retain_succession_expectation_v1=retain
                    driver.execute_step(ROOT_STEP,expected_revision=driver.frame['revision'])
                    if mode=='native_changed':
                        driver.frame['revision']+=1;driver.frame['native_revision']+=1;driver.frame['snapshot_id']='native:'+str(driver.frame['native_revision'])
                    elif mode=='date_changed':driver.frame['date_raw']+=24
                    elif mode=='date_changes_before_bundle_snapshot':driver.date_change_before_bundle_snapshot=True
                    service=GameplayBridgeService(driver);planned=service.plan_turn()
                    assert planned['plan']['selected_step']=='life-advance'
                    if mode=='old_3121_days':
                        previous=copy.deepcopy(driver.frame['succession_expectation'])
                        driver.frame.update(date_raw=driver.frame['date_raw']+3121*24,native_revision=driver.frame['native_revision']+1,revision=driver.frame['revision']+1)
                        driver.frame['snapshot_id']='native:'+str(driver.frame['native_revision'])
                        driver.execute_step(ROOT_STEP,expected_revision=driver.frame['revision']);service.plan_turn()
                        assert driver.frame['succession_expectation']['binding']['date_raw']-previous['binding']['date_raw']==3121*24
                    roots=driver.root_calls;retains=len(driver.retained_bundles);retained=copy.deepcopy(driver.frame['succession_expectation'])
                    service.plan_turn()
                    assert driver.root_calls==roots and len(driver.retained_bundles)==retains and driver.frame['succession_expectation']==retained
                    assert driver.requests==[] and driver.submit_calls==0
                    service_observations.append({'case':mode,'root_calls':roots,'retained_bundles':retains,'same_frame_replan_reused':True,'submissions':0,'complete_title_ids':[row['title']['title_id'] for row in retained['title_expectations']]})
            seam=original_tests.SuccessionTransitionContractTests();seam.setUp()
            before_expectation=freeze(seam.pre,episode_run_id='native-100-test',episode_character_id=100)
            for name,post in [('matched',copy.deepcopy(seam.post)),('distribution_mismatch',copy.deepcopy(seam.post))]:
                if name=='distribution_mismatch':post['succession_state']['value']['partition']['value']['title_heirs']=[original_tests._row(10,400,primary=True),original_tests._row(12,400,primary=False)]
                capture(producer_cases,producer_rejected,'native_reconcile_'+name,request('reconcile',seam.snapshot,post,before_expectation),produce)
            legacy=request('retain',{'snapshot_id':seam.pre['binding']['snapshot_id'],'revision':seam.pre['binding']['revision'],'native_revision':seam.pre['binding']['native_revision'],'date_raw':seam.pre['binding']['date_raw'],'episode_run_id':'native-100-test','episode_character_id':100,'paused':True,'one_life_terminal':False},seam.pre)
            for row in legacy['turn_bundle']['succession_state']['value']['partition']['value']['title_heirs']:row.pop('capital_province_id',None)
            capture(producer_cases,producer_rejected,'native_retain_legacy_three_field_rows',legacy,produce)
            base=copy.deepcopy(producer_cases[0]['request'])
            bad=[]
            for key in ('snapshot_id','revision','native_revision','date_raw'):
                value=copy.deepcopy(base);binding=value['turn_bundle']['binding'];binding[key]=binding[key]+'-different' if key=='snapshot_id' else binding[key]+1;bad.append(('crossed_'+key,value))
            value=copy.deepcopy(base);value['expected_revision']+=1;bad.append(('stale_expected_revision',value))
            value=copy.deepcopy(base);value['snapshot']['paused']=False;bad.append(('unpaused',value))
            value=copy.deepcopy(base);value['snapshot']['one_life_terminal']=True;bad.append(('terminal_living_projection',value))
            value=copy.deepcopy(base);value['snapshot']['episode_run_id']=None;bad.append(('missing_episode',value))
            value=copy.deepcopy(base);value['expected_revision']=True;bad.append(('boolean_revision',value))
            value=copy.deepcopy(base);value['expected_revision']=float(value['expected_revision']);bad.append(('floating_revision',value))
            for name,value in bad:capture(producer_cases,producer_rejected,name,value,produce,True)
            def fresh_request(reconciliation,expectation=None,living=None):return {'schema':'xar.java-succession-freshness-request/v1','reconciliation':copy.deepcopy(reconciliation),'expectation':copy.deepcopy(expectation),'last_living_frame':copy.deepcopy(living)}
            def observe(value):return freshness(value['reconciliation'],expectation=value['expectation'],last_living_frame=value['last_living_frame'])
            historical=json.loads(historical_path.read_bytes());rec=historical['reconciliation'];primary=historical['supplemental_living_heir_evidence']['normal_AUTO357']['planning_source_frame']
            last={key:primary[key] for key in ('snapshot_id','revision','native_revision','date_raw','episode_run_id')};last['episode_character_id']=primary['actor_character_id']
            capture(freshness_cases,freshness_rejected,'historical_3121_full_7_primary_never_combined',fresh_request(rec,living=last),observe)
            seed=before_expectation;boundary={key:seed['binding'][key] for key in ('snapshot_id','revision','native_revision','date_raw')};boundary.update(snapshot_id='native:boundary',revision=9,native_revision=25,date_raw=seed['binding']['date_raw']+7*24)
            reconciliation={'schema':'xar.ck3.succession-reconciliation/v1','status':'available','predecessor_binding':copy.deepcopy(seed['binding']),'predecessor_character_id':100,'successor_binding':boundary,'verdict':'matched'}
            for name,full,living in [('neither_observed',None,None),('full_without_last_living',seed,None),('complete_same_living',seed,seed['binding']),('complete_different_living',seed,{**seed['binding'],'snapshot_id':'native:later','native_revision':21,'date_raw':seed['binding']['date_raw']+24})]:
                capture(freshness_cases,freshness_rejected,name,fresh_request(reconciliation,full,living),observe)
            fbase=fresh_request(reconciliation,seed,seed['binding'])
            for key in ('snapshot_id','revision','native_revision','date_raw','episode_run_id','episode_character_id'):
                value=copy.deepcopy(fbase);binding=value['expectation']['binding'];binding[key]=binding[key]+'-different' if isinstance(binding[key],str) else binding[key]+1
                capture(freshness_cases,freshness_rejected,'expectation_other_'+key,value,observe,True)
            for name,change in [('other_episode',lambda value:value['last_living_frame'].update(episode_run_id='other-episode')),('living_after_boundary',lambda value:value['last_living_frame'].update(date_raw=value['reconciliation']['successor_binding']['date_raw']+1)),('boundary_before_source',lambda value:value['reconciliation']['successor_binding'].update(date_raw=value['expectation']['binding']['date_raw']-1)),('boolean_source_revision',lambda value:value['reconciliation']['predecessor_binding'].update(revision=True)),('floating_source_native_revision',lambda value:value['reconciliation']['predecessor_binding'].update(native_revision=20.0))]:
                value=copy.deepcopy(fbase);change(value);capture(freshness_cases,freshness_rejected,name,value,observe,True)
            def consumer_request(operation,**fields):return {'schema':'xar.java-succession-retained-consumer/v1','operation':operation,**copy.deepcopy(fields)}
            def consume(value):
                op=value['operation']
                if op=='retained_reader':return None if value['expectation'] is None else normalize(value['expectation'])
                if op=='wal_business':return json.loads(_business(value['fields']))
                if op=='saved_basis_flags':return parse_readonly_prefix_driver_flags_v1(value['flags']).to_wire()
                payload={'format_version':2,'pipe_name':'synthetic-m3-offline','bridge_pid':1,'episode_character_id':value['episode_character_id'],'episode_run_id':value['episode_run_id'],'command_history':[],'last_checkpoint':None,'rollback_war_failures':[],'succession_expectation':value['expectation']}
                restored=load_native_driver_state_for_resume_payload(payload,'synthetic-m3-offline')
                assert restored is not None
                return restored['succession_expectation']
            flags={'managed_restore_transaction':None,'rollback_war_failure':None,'succession_expectation':seed,'rollback_war_failures':[],'session_binding_present':False}
            values=[('restore_complete',consumer_request('restore',expectation=seed,episode_run_id='native-100-test',episode_character_id=100)),('restore_null',consumer_request('restore',expectation=None,episode_run_id=None,episode_character_id=None)),('retained_reader_complete',consumer_request('retained_reader',expectation=seed)),('retained_reader_null',consumer_request('retained_reader',expectation=None)),('wal_complete_business',consumer_request('wal_business',fields={'succession_expectation':seed,'episode_character_id':100,'nullable_extension':None,'empty_extension':[]})),('saved_basis_complete',consumer_request('saved_basis_flags',flags=flags)),('saved_basis_null',consumer_request('saved_basis_flags',flags={**flags,'succession_expectation':None}))]
            for name,value in values:capture(consumer_cases,consumer_rejected,name,value,consume)
            for key in ('episode_run_id','episode_character_id'):
                value=copy.deepcopy(values[0][1]);value[key]='other-episode' if key=='episode_run_id' else 101;capture(consumer_cases,consumer_rejected,'restore_wrong_'+key,value,consume,True)
            value=copy.deepcopy(values[-2][1]);value['flags']['session_binding_present']=True;capture(consumer_cases,consumer_rejected,'saved_basis_pending_binding',value,consume,True)
            value=copy.deepcopy(values[4][1]);value['fields']['succession_expectation']['title_expectations'][0]['first_heir_character_id']=True;capture(consumer_cases,consumer_rejected,'wal_boolean_heir',value,consume,True)
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            after=refs()
            if before!=after:raise RuntimeError('original source/fixture changed during M3 capture')
            runtime_dependencies=(root/'tools/.venv').resolve()
            imported={Path(module.__file__).resolve() for module in list(sys.modules.values()) if getattr(module,'__file__',None) and str(module.__file__).endswith('.py') and Path(module.__file__).resolve().is_relative_to(root) and not Path(module.__file__).resolve().is_relative_to(runtime_dependencies)}
            if not imported<=paths:raise RuntimeError('original capture imported an unpinned repository source: '+str(sorted(imported-paths)))
            compatibility_name=str(compatibility_test.relative_to(root)).replace('\\\\','/') if compatibility_test.is_relative_to(root) else str(compatibility_test)
            compatibility_ref=next(row for row in before if row['path']==compatibility_name)
            original_ref=next(row for row in before if row['path']=='ck3_autonomous_player/tests/unit/test_r76_initial_succession_root_reuse.py')
            fixture_metadata={'compatibility_test_fixture_ref':compatibility_ref,'repository_test_baseline_ref':original_ref,'compatibility_fixture_loaded_explicitly':True,'unmodified_repository_fixture_previously_red':True,'runtime_dependency_root_excluded_from_project_source_pins':str(runtime_dependencies),'python_executable':sys.executable,'python_version':sys.version}
            print(json.dumps({**fixture_metadata,'schema':'xar.g2.m3.original-producer-golden/v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),'synthetic_fixture':True,'scope':'Actual Service root materializer and full bundles plus actual Native retain/reconcile and original retained readers; synthetic backend, in-memory owner/lock and persistence callback only. One explicit test-only provenance comparison fixture retains the original complete business assertion; two focused original tests are unchanged. No Game/native pipe/campaign Driver/SAVE IO, no action or ledger authority.','fixture_root':str(scratch),'source_refs':before,'source_refs_unchanged':True,'original_unittest':{'tests':run.testsRun,'failures':len(run.failures),'errors':len(run.errors),'skipped':len(run.skipped),'focused_original_tests':2,'focused_compatibility_fixture_tests':1,'full_service_tests_executed':2},'service_observations':service_observations,'producer_cases':producer_cases,'producer_rejected':producer_rejected,'freshness_cases':freshness_cases,'freshness_rejected':freshness_rejected,'consumer_cases':consumer_cases,'consumer_rejected':consumer_rejected},ensure_ascii=False,separators=(',',':'),allow_nan=False))
            """;
}
