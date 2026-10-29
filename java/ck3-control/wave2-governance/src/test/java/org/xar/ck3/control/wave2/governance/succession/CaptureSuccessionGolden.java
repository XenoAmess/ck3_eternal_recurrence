package org.xar.ck3.control.wave2.governance.succession;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Explicit offline original-producer capture, executed only by the shared storage/M7 owner. */
public final class CaptureSuccessionGolden {
    private CaptureSuccessionGolden() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 4) { throw new IllegalArgumentException("repository-root existing-python new-output-json approved-scratch"); }
        Path root = Path.of(arguments[0]).toRealPath(); Path output = Path.of(arguments[2]).toAbsolutePath().normalize();
        Path temporary = Path.of(arguments[3]).toRealPath();
        if (!Files.isDirectory(temporary) || !output.startsWith(temporary)) { throw new IllegalArgumentException("capture output must stay under approved scratch"); }
        if (Files.exists(output)) { throw new IllegalArgumentException("original capture must not be overwritten"); }
        ProcessBuilder builder = new ProcessBuilder(List.of(arguments[1], "-B", "-X", "utf8", "-c", SCRIPT, root.toString())).directory(root.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.environment().put("XAR_REPO_ROOT", root.toString());
        builder.environment().put("PYTHONUTF8", "1"); builder.environment().put("PYTHONIOENCODING", "utf-8");
        for (String key : List.of("TEMP", "TMP", "TMPDIR")) { builder.environment().put(key, temporary.toString()); }
        Process process = builder.start();
        byte[] bytes;
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var read = executor.submit(() -> process.getInputStream().readNBytes(120_001));
            if (!process.waitFor(60, TimeUnit.SECONDS)) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); throw new IllegalStateException("original succession capture timed out"); }
            bytes = read.get(5, TimeUnit.SECONDS);
        } finally { if (process.isAlive()) { process.destroyForcibly(); } }
        if (process.exitValue() != 0 || bytes.length == 0 || bytes.length > 120_000) { throw new IllegalStateException("original succession capture failed: exit=" + process.exitValue() + ", bytes=" + bytes.length); }
        StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes));
        Files.createDirectories(output.getParent()); Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
        System.out.println("Original succession producer captured " + bytes.length + " bytes at " + output);
    }
    private static final String SCRIPT = """
            import sys,json,copy,hashlib,subprocess,datetime,importlib.util,unittest
            from pathlib import Path
            root=Path(sys.argv[1]);sys.path.insert(0,str(root));sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            relatives=['ck3_autonomous_player/src/xar_autoplayer/bridge/succession_transition_contract.py','ck3_autonomous_player/src/xar_autoplayer/ordinary_succession_operating_context_v1.py','ck3_autonomous_player/tests/unit/test_succession_transition_contract.py','ck3_autonomous_player/tests/unit/test_ordinary_succession_operating_context_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/src/xar_autoplayer/bridge/succession_binding_refresh_wal_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/succession_expectation_invalidation_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/succession_warm_publication_refresh_v1.py','tools/g2_saved_campaign/current_saved_basis_v1.py']
            relatives+=['tools/g2_saved_campaign/file_stat_identity_v1.py','tools/ck3_live_run_id.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py']
            relatives+=['ck3_autonomous_player/src/xar_autoplayer/bridge/turn_bundle_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/campaign_root_context_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/driver.py','ck3_autonomous_player/src/xar_autoplayer/strategy.py','ck3_autonomous_player/src/xar_autoplayer/family_marriage_episode_handoff_v1.py']
            relatives+=['ck3_autonomous_player/tests/unit/test_turn_bundle_v1.py']
            relatives+=['ck3_autonomous_player/src/xar_autoplayer/environment.py','ck3_autonomous_player/src/xar_autoplayer/native_session.py','ck3_autonomous_player/src/xar_autoplayer/bridge/driver_state_wal_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_decision_outcome_contract.py']
            def refs():return [{'path':p,'bytes':len((root/p).read_bytes()),'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in relatives]
            before=refs()
            def module(name,path):
                spec=importlib.util.spec_from_file_location(name,root/path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
            tests=module('original_succession_tests',relatives[2]);operating_tests=module('original_succession_operating_tests',relatives[3])
            original_suite=unittest.defaultTestLoader.loadTestsFromModule(tests)
            def test_ids(suite):
                for item in suite:
                    if isinstance(item,unittest.TestSuite):yield from test_ids(item)
                    else:yield item.id()
            names=list(test_ids(original_suite))
            result=unittest.TextTestRunner(stream=sys.stderr).run(original_suite)
            if not result.wasSuccessful() or result.testsRun!=len(names) or result.skipped:sys.exit(2)
            operating_tests.test_complete_current_estate_changes_risks_and_frame_invalidation()
            from xar_autoplayer.bridge.succession_transition_contract import freeze_succession_expectation_v1 as freeze,normalize_succession_expectation_v1 as normalize,reconcile_succession_transition_v1 as reconcile
            from xar_autoplayer.ordinary_succession_operating_context_v1 import build_ordinary_succession_operating_context_v1 as operating
            from xar_autoplayer.bridge.succession_binding_refresh_wal_v1 import _expectation as wal_expectation
            from tools.g2_saved_campaign.current_saved_basis_v1 import parse_readonly_prefix_driver_flags_v1 as prefix_flags
            from xar_autoplayer.bridge import native_driver
            from xar_autoplayer.bridge import succession_expectation_invalidation_v1 as invalidation,succession_warm_publication_refresh_v1 as warm
            from xar_autoplayer.bridge.turn_bundle_contract import build_turn_bundle_v1
            from unittest import mock
            seam=tests.SuccessionTransitionContractTests();seam.setUp();pre=seam.pre;post=seam.post;snapshot=seam.snapshot
            expectation=freeze(pre,episode_run_id='native-100-test',episode_character_id=100)
            def request(op,**fields):return {'schema':'xar.java-succession-request/v1','operation':op,**copy.deepcopy(fields)}
            def execute(value):
                op=value['operation']
                if op=='freeze':return freeze(value['turn_bundle'],episode_run_id=value['episode_run_id'],episode_character_id=value['episode_character_id'])
                if op=='normalize':return normalize(value['expectation'])
                if op=='reconcile':return reconcile(value['expectation'],value['post_snapshot'],value['post_turn_bundle'])
                return operating(value['snapshot'],previous_expectation=value['previous_expectation'])
            cases=[]
            def consume(function,value):
                try:return {'accepted':True,'output':function(copy.deepcopy(value))}
                except ValueError:return {'accepted':False,'output':None}
            def add(name,value):
                expected=execute(value)
                if value['operation'] in ('freeze','normalize') and normalize(expected)!=expected:raise RuntimeError('original retained-state consumer changed producer')
                consumers=None
                if value['operation'] in ('freeze','normalize'):
                    flags={'managed_restore_transaction':None,'rollback_war_failure':None,'succession_expectation':expected,'rollback_war_failures':[],'session_binding_present':False}
                    consumers={'binding_refresh_wal':consume(wal_expectation,{'succession_expectation':expected}),'readonly_prefix_driver_flags':consume(lambda v:prefix_flags(v).to_wire(),flags)}
                    if not consumers['binding_refresh_wal']['accepted']:raise RuntimeError('actual WAL consumer rejected original expectation')
                cases.append({'name':name,'request':value,'expected':expected,'actual_consumers':consumers})
            add('freeze_original_complete_current_rows',request('freeze',turn_bundle=pre,episode_run_id='native-100-test',episode_character_id=100))
            legacy=copy.deepcopy(pre)
            for row in legacy['succession_state']['value']['partition']['value']['title_heirs']:row.pop('capital_province_id')
            add('freeze_legacy_three_field_rows',request('freeze',turn_bundle=legacy,episode_run_id='native-100-test',episode_character_id=100))
            add('normalize_complete_retained_expectation',request('normalize',expectation=expectation))
            large=copy.deepcopy(expectation);large['binding'].update(revision=2**64-1,native_revision=2**63+1);large['title_expectations'][0]['title']['sdk_extension']={'fractional':1.25,'nullable':None,'empty':[]}
            add('normalize_uint64_and_extensible_title',request('normalize',expectation=large))
            noheir=copy.deepcopy(pre);noheir['succession_state']['value']['primary_title_heir_character_id']={'status':'not_applicable','value':None,'unavailable_reason':'no_observed_primary_title_successor'};noheir['succession_state']['value']['partition']['value']['risk_state']='no_primary_heir'
            for row in noheir['succession_state']['value']['partition']['value']['title_heirs']:row['first_heir_character_id']=None
            add('freeze_no_primary_heir',request('freeze',turn_bundle=noheir,episode_run_id='native-100-test',episode_character_id=100))
            rec=request('reconcile',expectation=expectation,post_snapshot=snapshot,post_turn_bundle=post);add('reconcile_actual_successor_and_additional_title',rec)
            wrong=copy.deepcopy(rec);wrong['post_snapshot']['played_character']['character_id']=300;wrong['post_turn_bundle']['ruler_state']['value']['character_id']=300;add('reconcile_unexpected_actual_successor',wrong)
            changed=copy.deepcopy(rec);changed['post_turn_bundle']['succession_state']['value']['partition']['value']['title_heirs']=[tests._row(10,400,primary=True),tests._row(12,400,primary=False)];add('reconcile_missing_expected_and_unexpected_retained',changed)
            unknown=copy.deepcopy(rec);unknown['expectation']=freeze(noheir,episode_run_id='native-100-test',episode_character_id=100);add('reconcile_no_observed_heir_never_invents_one',unknown)
            living={**expectation['binding'],'paused':True,'map_ready':True,'one_life_terminal':False,'one_life_terminal_reason':None,'played_character':{'character_id':100,'alive':True},'active_event':None,'pending_character_interaction':None,'succession_lifecycle':{'lifecycle':'ordinary_campaign_succession'},'succession_expectation':copy.deepcopy(expectation)}
            add('operating_retained_same_frame_estate',request('operating',snapshot=living,previous_expectation=None))
            add('operating_non_object_snapshot',request('operating',snapshot=None,previous_expectation=None))
            stale=copy.deepcopy(living);stale['native_revision']+=1;add('operating_stale_same_published_frame',request('operating',snapshot=stale,previous_expectation=None))
            pending=copy.deepcopy(living);pending['active_event']={'instance_id':7};add('operating_pending_decision',request('operating',snapshot=pending,previous_expectation=None))
            unbound=copy.deepcopy(living);unbound['succession_lifecycle']['lifecycle']='unknown';add('operating_unknown_lifecycle',request('operating',snapshot=unbound,previous_expectation=None))
            nextone=copy.deepcopy(living);nextone.update(snapshot_id='native:21',revision=8,native_revision=21);nextone['succession_expectation']['binding'].update(snapshot_id='native:21',revision=8,native_revision=21);nextone['succession_expectation']['title_expectations'][1]['first_heir_character_id']=300;nextone['succession_expectation']['title_expectations'].append({'title':{'title_id':30,'tier_raw':4},'first_heir_character_id':300,'primary':False})
            add('operating_estate_changes_are_not_law_changes',request('operating',snapshot=nextone,previous_expectation=expectation))
            prior=copy.deepcopy(expectation);prior['binding']['episode_run_id']='different';add('operating_other_episode_previous_not_comparable',request('operating',snapshot=living,previous_expectation=prior))
            unknownrank=copy.deepcopy(living);unknownrank['succession_expectation']['title_expectations'][2]['title']['tier_raw']=2.0;add('operating_float_rank_stays_unknown',request('operating',snapshot=unknownrank,previous_expectation=None))
            none=copy.deepcopy(living);none['succession_expectation']=freeze(noheir,episode_run_id='native-100-test',episode_character_id=100);add('operating_no_primary_heir',request('operating',snapshot=none,previous_expectation=None))
            witnessed=[]
            def driver_freeze(bundle,*,episode_run_id,episode_character_id):
                value=request('freeze',turn_bundle=bundle,episode_run_id=episode_run_id,episode_character_id=episode_character_id);expected=execute(value)
                witnessed.append({'request':value,'expected':copy.deepcopy(expected)});return expected
            def driver_normalize(expectation):
                value=request('normalize',expectation=expectation);expected=execute(value)
                witnessed.append({'request':value,'expected':copy.deepcopy(expected)});return expected
            def driver_reconcile(expectation,post_snapshot,post_turn_bundle):
                value=request('reconcile',expectation=expectation,post_snapshot=post_snapshot,post_turn_bundle=post_turn_bundle);expected=execute(value)
                witnessed.append({'request':value,'expected':copy.deepcopy(expected)});return expected
            with mock.patch.object(native_driver,'freeze_succession_expectation_v1',side_effect=driver_freeze),mock.patch.object(native_driver,'normalize_succession_expectation_v1',side_effect=driver_normalize),mock.patch.object(native_driver,'reconcile_succession_transition_v1',side_effect=driver_reconcile):
                consumer_result=unittest.TextTestRunner(stream=sys.stderr).run(unittest.TestSuite([tests.SuccessionTransitionContractTests('test_native_driver_retains_restores_and_reconciles_expectation')]))
            if not consumer_result.wasSuccessful() or consumer_result.testsRun!=1 or consumer_result.skipped:sys.exit(3)
            if {row['request']['operation'] for row in witnessed}!={'freeze','normalize','reconcile'}:raise RuntimeError('actual Driver/Service fixture did not reach all original producer boundaries')
            driver_witnessed=copy.deepcopy(witnessed);witnessed=[]
            bundle_tests=module('original_succession_bundle_fixture','ck3_autonomous_player/tests/unit/test_turn_bundle_v1.py')
            current=bundle_tests._snapshot();current.update(episode_run_id='offline-succession-root-consumer',episode_character_id=current['played_character']['character_id'],map_ready=True,one_life_terminal=False,one_life_terminal_reason=None)
            root_material=bundle_tests._root()
            complete_bundle=build_turn_bundle_v1(current,root_material)
            if complete_bundle['readiness']['succession_partition_ready'] is not True:raise RuntimeError('original full partition fixture is incomplete')
            # Explicit offline scene enrichment; completeness is derived by the original bundle validator, never live qualification.
            root_material['campaign_root_context']['readiness']={'held_title_partition_ready':complete_bundle['readiness']['succession_partition_ready']}
            retained=freeze(complete_bundle,episode_run_id=current['episode_run_id'],episode_character_id=current['episode_character_id'])
            state={'expectation':retained,'reconciliation':{'opaque_prior_projection':True}};preserved=copy.deepcopy(state)
            with mock.patch.object(invalidation,'freeze_succession_expectation_v1',side_effect=driver_freeze),mock.patch.object(invalidation,'normalize_succession_expectation_v1',side_effect=driver_normalize),mock.patch.object(warm,'freeze_succession_expectation_v1',side_effect=driver_freeze),mock.patch.object(warm,'normalize_succession_expectation_v1',side_effect=driver_normalize):
                unchanged=invalidation.invalidate_succession_state_from_root_v1(state,snapshot=current,campaign_root_result=root_material)
                prior_epoch=copy.deepcopy(state);prior_epoch['expectation']['binding']['revision']=current['revision']+10
                refreshed=warm.same_pid_hot_publication_refresh_v1(prior_epoch,snapshot=current,campaign_root_result=root_material,restore_kind='same_pid_hot')
            if state!=preserved or unchanged['status']!='unchanged' or refreshed is None or refreshed['status']!='source_epoch_refresh_required':raise RuntimeError('actual completed-root consumers did not preserve their source/epoch semantics')
            root_consumers={'invalidation':unchanged,'warm_publication_refresh':refreshed}
            after=refs()
            if before!=after:raise RuntimeError('original succession source changed during capture')
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            print(json.dumps({'schema':'xar.java-succession-original-producer-golden/v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Offline original producer functions, actual WAL/readonly-prefix/invalidation/warm pure readers, plus the unchanged original Driver/Service retain/persist/restore/reconcile/continuation test over fake endpoints and temporary fixture state. Root materials come from the unchanged original turn-bundle test helpers. No Game, Steam, live native pipe, canonical ledger, SDK Driver or SAVE access. Operating context has no active production caller. Fixture continuation grants no live continuation authority.','source_refs':before,'source_refs_unchanged':True,'original_unittest':{'whole_module':True,'discovered_tests':len(names),'discovered_test_ids':names,'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'operating_compound_function_executed':True},'consumer_unittest':{'method':'test_native_driver_retains_restores_and_reconciles_expectation','tests':consumer_result.testsRun,'failures':len(consumer_result.failures),'errors':len(consumer_result.errors),'skipped':len(consumer_result.skipped)},'actual_driver_consumer_requests':driver_witnessed,'actual_root_consumer_requests':witnessed,'actual_root_consumer_outputs':root_consumers,'cases':cases},ensure_ascii=False,separators=(',',':'),allow_nan=False))
            """;
}
