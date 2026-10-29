package org.xar.ck3.control.wave2.governance.government;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Explicit original-producer capture; default JUnit never invokes this tool. */
public final class CaptureGovernmentGolden {
    private static final int MAXIMUM_BYTES = 100_000;
    private CaptureGovernmentGolden() { }

    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) { throw new IllegalArgumentException("repository-root existing-python output-json"); }
        Path root = Path.of(arguments[0]).toRealPath();
        Path output = Path.of(arguments[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) { throw new IllegalArgumentException("capture never overwrites an original"); }
        Process child = new ProcessBuilder(List.of(arguments[1], "-B", "-c", SCRIPT, root.toString()))
                .directory(root.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT).start();
        byte[] raw;
        try (var readers = Executors.newVirtualThreadPerTaskExecutor()) {
            var read = readers.submit(() -> child.getInputStream().readNBytes(MAXIMUM_BYTES + 1));
            if (!child.waitFor(Duration.ofSeconds(60).toMillis(), TimeUnit.MILLISECONDS)) {
                child.descendants().forEach(ProcessHandle::destroyForcibly); child.destroyForcibly();
                throw new IllegalStateException("original government producer capture timed out");
            }
            raw = read.get(5, TimeUnit.SECONDS);
        } finally {
            if (child.isAlive()) { child.destroyForcibly(); }
        }
        if (child.exitValue() != 0 || raw.length == 0 || raw.length > MAXIMUM_BYTES) {
            throw new IllegalStateException("original government capture failed: exit=" + child.exitValue() + ", bytes=" + raw.length);
        }
        Files.createDirectories(output.getParent()); Files.write(output, raw, StandardOpenOption.CREATE_NEW);
        System.out.println("Captured original government producer: " + raw.length + " bytes at " + output);
    }

    private static final String SCRIPT = """
            import sys,json,hashlib,subprocess,unittest,importlib.util,copy,datetime
            from pathlib import Path
            root=Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            relatives=['ck3_autonomous_player/src/xar_autoplayer/ordinary_campaign_government_context_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/government_runtime_adapter_private_transport.py','ck3_autonomous_player/src/xar_autoplayer/strategy.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','ck3_autonomous_player/src/xar_autoplayer/bridge/nonwar_private_build.py','ck3_autonomous_player/tests/unit/test_ordinary_campaign_government_context_leaf_v1.py','ck3_autonomous_player/tests/fixtures/ck3_12002_government_protocol_live_fix/hello.json','ck3_autonomous_player/tests/fixtures/ck3_12002_government_protocol_live_fix/initial-state.json','ck3_autonomous_player/tests/fixtures/ck3_12002_government_protocol_live_fix/government-response-red.json']
            def refs():
                return [{'path':rel,'bytes':len((root/rel).read_bytes()),'sha256':hashlib.sha256((root/rel).read_bytes()).hexdigest()} for rel in relatives]
            before=refs()
            spec=importlib.util.spec_from_file_location('original_government_context_tests',root/relatives[5]);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            result=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(unittest.defaultTestLoader.loadTestsFromModule(module))
            if not result.wasSuccessful() or result.testsRun!=3 or result.skipped:sys.exit(2)
            from xar_autoplayer.ordinary_campaign_government_context_v1 import build_ordinary_campaign_government_context_v1 as build
            base_snapshot,base_observation=module._ordinary_fixture_inputs()
            def projected(snapshot):
                value={k:copy.deepcopy(snapshot[k]) for k in ('native_revision','date_raw','campaign_goal') if k in snapshot}
                if 'played_character' in snapshot:value['played_character']={'character_id':snapshot['played_character']['character_id']}
                if 'succession_lifecycle' in snapshot:value['succession_lifecycle']={'lifecycle':snapshot['succession_lifecycle']['lifecycle']}
                hello=snapshot['diagnostics']['hello'];value['diagnostics']={'hello':{k:copy.deepcopy(hello[k]) for k in ('expected_ck3_version','expected_ck3_sha256','game_version','executable_sha256') if k in hello}}
                return value
            base_request={'schema':'xar.java-government-context-request/v1','snapshot':projected(base_snapshot),'government_observation':copy.deepcopy(base_observation),'query_permitted':True}
            def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()
            def patch(before,after,path=''):
                if isinstance(before,dict) and isinstance(after,dict):
                    changes=[]
                    for key in before.keys()-after.keys():changes.append({'op':'remove','path':path+'/'+key})
                    for key in after:
                        at=path+'/'+key
                        if key not in before:changes.append({'op':'set','path':at,'value':after[key]})
                        elif before[key]!=after[key]:changes.extend(patch(before[key],after[key],at))
                    return changes
                return [] if before==after else [{'op':'set','path':path,'value':after}]
            cases=[]
            def add(name,mutator=None,permitted=True,observation_present=True):
                snapshot=copy.deepcopy(base_snapshot);observed=copy.deepcopy(base_observation)
                if mutator:mutator(snapshot,observed)
                if not observation_present:observed=None
                expected=build(snapshot,government_observation=observed,query_permitted=permitted)
                request={'schema':'xar.java-government-context-request/v1','snapshot':projected(snapshot),'government_observation':observed,'query_permitted':permitted}
                actual_observation=expected.pop('government_runtime_adapter')
                if actual_observation is not None and actual_observation!=observed:raise RuntimeError('original normalizer altered the supplied primitive')
                cases.append({'name':name,'request_patch':patch(base_request,request),'expected':expected,'expected_observation_sha256':None if actual_observation is None else digest(actual_observation)})
            add('actual_primitive_core_identity_44_features')
            add('default_query_off',permitted=False)
            add('inactive_lifecycle',lambda s,o:s['succession_lifecycle'].update(lifecycle='fixture_other_lifecycle'))
            add('missing_goal',lambda s,o:s.pop('campaign_goal'))
            add('malformed_goal_origin_zero',lambda s,o:s['campaign_goal'].update(origin_character_id=0))
            add('missing_government_observation',observation_present=False)
            def spec_only(s,o):
                o['government']['key']='japan_feudal_government'
                o['adapter'].update(status='adapter_spec_ready_not_implemented',family='tgp_japan_feudal',requirements_met=True,required_effective_features=[],capability_profile_features=[copy.deepcopy(row) for row in o['effective_feature_flags']['items'] if row['key'] in {'all_under_heaven','advanced_aspirations'}])
                o['readiness']['core_adapter_ready']=False
            add('synthetic_spec_only_native_verdict',spec_only)
            add('valid_goal_but_different_current_actor',lambda s,o:s['campaign_goal'].update(current_character_id=s['played_character']['character_id']+1))
            add('stale_native_revision',lambda s,o:o.update(snapshot_revision=o['snapshot_revision']+1))
            add('wrong_known_build',lambda s,o:o['build'].update(version='1.20.0.3',exe_sha256='94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6'))
            add('wrong_native_provenance',lambda s,o:o['provenance'].update(feature_backend_id='fixture-wrong-provider'))
            add('duplicate_feature_key',lambda s,o:o['effective_feature_flags']['items'][1].update(key=o['effective_feature_flags']['items'][0]['key']))
            add('native_core_verdict_disagrees',lambda s,o:o['readiness'].update(core_adapter_ready=False))
            def unavailable(s,o):
                o.update(status='unavailable',unavailable_reason='fixture_native_unavailable');o['readiness'].update(same_frame_ready=False,core_adapter_ready=False)
            add('native_unavailable_retained',unavailable)
            def absent(s,o):o.update(status='not_present');o['readiness'].update(core_adapter_ready=False)
            add('native_not_present_never_core_ready',absent)
            rejects=[]
            def reject(name,mutator):
                snapshot=copy.deepcopy(base_snapshot);observed=copy.deepcopy(base_observation);mutator(snapshot,observed)
                request={'schema':'xar.java-government-context-request/v1','snapshot':projected(snapshot),'government_observation':observed,'query_permitted':True}
                legacy=build(snapshot,government_observation=observed,query_permitted=True)
                rejects.append({'name':name,'raw_request_json':json.dumps(request,ensure_ascii=False,separators=(',',':'),allow_nan=False),'legacy_result_projection':{key:legacy[key] for key in ('status','identity_observation_ready','core_adapter_ready','ordinary_goal_context_ready','unavailable_reason')},'expected_java_wire_rejection':True})
            reject('boolean_schema_version',lambda s,o:o.update(schema_version=True))
            reject('float_observation_revision',lambda s,o:o.update(snapshot_revision=3.0))
            reject('float_native_feature_count',lambda s,o:o['effective_feature_flags'].update(native_count=44.0))
            reject('float_native_feature_index',lambda s,o:o['effective_feature_flags']['items'][0].update(native_index=0.0))
            reject('float_player_character_id',lambda s,o:o.update(player_character_id=29829.0))
            after=refs()
            if before!=after:raise RuntimeError('original government producer source changed during capture')
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            value={'schema':'xar.java-government-context-original-producer-golden/v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'historical_observation_machine_id':'unknown','scope':'Actual existing NativeProtocolState ingest helper, current normalizer and context builder. Outer RED government envelope remains historical RED; nested primitive is reused, ordinary lifecycle/goal and scenario variations are explicit offline fixture seams. No live query or game action. Repeated requests are exact base+patch; preserved original-result observation is represented by its actual SHA-256, not an inferred readiness verdict.','source_refs':before,'source_refs_unchanged':before==after,'original_unittest':{'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped)},'base_request':base_request,'cases':cases,'wire_rejections':rejects}
            print(json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False))
            """;
}
