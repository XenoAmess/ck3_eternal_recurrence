package org.xar.ck3.control.wave3.governance.lifecycle;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.ByteBuffer;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Explicit bounded original-producer and actual pure-consumer capture for storage/M7 only. */
public final class CaptureSuccessionLifecycleGolden {
    private CaptureSuccessionLifecycleGolden() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 4) { throw new IllegalArgumentException("repository-root existing-python new-output-json approved-scratch"); }
        Path root = Path.of(arguments[0]).toRealPath(); Path output = Path.of(arguments[2]).toAbsolutePath().normalize();
        Path temporary = Path.of(arguments[3]).toRealPath();
        if (!Files.isDirectory(temporary) || !output.startsWith(temporary)) { throw new IllegalArgumentException("capture output must stay under approved scratch"); }
        if (Files.exists(output)) { throw new IllegalArgumentException("cannot overwrite original capture"); }
        ProcessBuilder builder = new ProcessBuilder(List.of(arguments[1], "-B", "-X", "utf8", "-c", SCRIPT, root.toString())).directory(root.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1"); builder.environment().put("XAR_REPO_ROOT", root.toString());
        builder.environment().put("PYTHONUTF8", "1"); builder.environment().put("PYTHONIOENCODING", "utf-8");
        for (String key : List.of("TEMP", "TMP", "TMPDIR")) { builder.environment().put(key, temporary.toString()); }
        Process process = builder.start(); byte[] bytes;
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var read = executor.submit(() -> process.getInputStream().readNBytes(60_001));
            if (!process.waitFor(60, TimeUnit.SECONDS)) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); throw new IllegalStateException("lifecycle original capture timed out"); }
            bytes = read.get(5, TimeUnit.SECONDS);
        } finally { if (process.isAlive()) { process.destroyForcibly(); } }
        if (process.exitValue() != 0 || bytes.length == 0 || bytes.length > 60_000) { throw new IllegalStateException("lifecycle original capture failed: exit=" + process.exitValue() + ", bytes=" + bytes.length); }
        StandardCharsets.UTF_8.newDecoder().onMalformedInput(CodingErrorAction.REPORT).onUnmappableCharacter(CodingErrorAction.REPORT).decode(ByteBuffer.wrap(bytes));
        Files.createDirectories(output.getParent()); Files.write(output, bytes, StandardOpenOption.CREATE_NEW); System.out.println("Original lifecycle capture: " + bytes.length + " bytes at " + output);
    }
    private static final String SCRIPT = """
            import sys,json,copy,hashlib,subprocess,datetime,importlib.util,unittest
            from pathlib import Path
            root=Path(sys.argv[1]);sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            relatives=['ck3_autonomous_player/src/xar_autoplayer/bridge/succession_transition_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','ck3_autonomous_player/src/xar_autoplayer/cold_checkpoint_validator.py','ck3_autonomous_player/src/xar_autoplayer/checkpoint_environment_rebinder.py','ck3_autonomous_player/src/xar_autoplayer/ordinary_seed_rebinder.py','ck3_autonomous_player/src/xar_autoplayer/rogue_checkpoint_rebinder.py','ck3_autonomous_player/src/xar_autoplayer/strategy.py']
            relatives+=['tools/ck3_live_run_id.py','ck3_autonomous_player/src/xar_autoplayer/errors.py']
            unit_paths=['ck3_autonomous_player/tests/unit/test_checkpoint_environment_rebinder.py','ck3_autonomous_player/tests/unit/test_ordinary_seed_rebinder.py','ck3_autonomous_player/tests/unit/test_rogue_checkpoint_rebinder.py','ck3_autonomous_player/tests/unit/test_cold_checkpoint_type_contract.py']
            relatives+=unit_paths
            relatives+=['ck3_autonomous_player/src/xar_autoplayer/environment.py','ck3_autonomous_player/src/xar_autoplayer/native_session.py','ck3_autonomous_player/src/xar_autoplayer/one_generation_preflight.py','ck3_autonomous_player/src/xar_autoplayer/cli.py']
            def refs():return [{'path':p,'bytes':len((root/p).read_bytes()),'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in relatives]
            before=refs()
            unit_suite=unittest.TestSuite()
            for index,path in enumerate(unit_paths):
                spec=importlib.util.spec_from_file_location('lifecycle_original_module_'+str(index),root/path)
                module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
                unit_suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
            def test_ids(suite):
                for item in suite:
                    if isinstance(item,unittest.TestSuite):yield from test_ids(item)
                    else:yield item.id()
            ids=list(test_ids(unit_suite))
            unit_result=unittest.TextTestRunner(stream=sys.stderr).run(unit_suite)
            if not unit_result.wasSuccessful() or unit_result.testsRun!=len(ids) or unit_result.skipped or not ids:sys.exit(2)
            from xar_autoplayer.bridge.succession_transition_contract import normalize_succession_lifecycle_binding_v1 as normalize,legacy_rogue_one_life_binding_v1 as legacy,unknown_succession_lifecycle_binding_v1 as unknown
            from xar_autoplayer.checkpoint_environment_rebinder import _checkpoint_binding
            from xar_autoplayer.ordinary_seed_rebinder import _ordinary_binding,_source_lifecycle_anchors as ordinary_anchors
            from xar_autoplayer.rogue_checkpoint_rebinder import _rogue_binding,_source_lifecycle_anchors as rogue_anchors
            from xar_autoplayer.errors import AgentError
            def payload(binding):
                return {'format_version':2,'succession_lifecycle':copy.deepcopy(binding),'last_checkpoint':{'history_index':1,'succession_lifecycle':copy.deepcopy(binding)},'command_history':[{'index':1,'command':'save-checkpoint','ok':True,'result':{'checkpoint':{'succession_lifecycle':copy.deepcopy(binding)}}}]}
            def consumer(function,value):
                try:return {'accepted':True,'binding':function(value)}
                except (ValueError,AgentError):return {'accepted':False,'binding':None}
            cases=[]
            def add(name,binding,operation='normalize'):
                expected=normalize(binding)
                request={'schema':'xar.java-succession-lifecycle-request/v1','operation':operation}
                if operation=='normalize':request['binding']=copy.deepcopy(binding)
                cases.append({'name':name,'request':request,'expected':expected,'actual_consumers':{'checkpoint_environment_binding':consumer(_checkpoint_binding,payload(expected)),'ordinary_seed_binding':consumer(lambda v:_ordinary_binding(v,'capture'),expected),'rogue_checkpoint_binding':consumer(lambda v:_rogue_binding(v,'capture'),expected)}})
            add('legacy_rogue_constructor',legacy(),'legacy');add('unknown_constructor',unknown(),'unknown')
            ordinary={'schema':'xar.ck3.succession-lifecycle-binding/v1','lifecycle':'ordinary_campaign_succession','xar_enabled':'xar_off','pact_contract':'absent_by_fresh_campaign_xar_off_contract','source':'prepared-environment-manifest','environment_sha256':'a'*64}
            add('frozen_ordinary_xar_off',ordinary)
            absent={**ordinary,'xar_enabled':None,'pact_contract':'absent_by_verified_xar_mod_not_loaded','source':'absent_by_verified_xar_mod_not_loaded'};add('ordinary_verified_mod_absence_binding',absent)
            add('prepared_rogue_binding',{**legacy(),'source':'prepared-environment-manifest','environment_sha256':'b'*64})
            add('normalizer_rogue_custom_source_still_rejected_by_rebinder',{**legacy(),'source':'original-custom-source','environment_sha256':'c'*64})
            add('normalizer_unknown_preserves_optional_digest_and_source',{**unknown(),'source':'explicit-unclassified-source','environment_sha256':'d'*64})
            add('normalizer_legacy_source_with_digest_is_not_exact_rebinder_legacy',{**legacy(),'environment_sha256':'a'*64})
            invalid=[]
            def reject(name,value):
                try:normalize(value)
                except (ValueError,TypeError):invalid.append({'name':name,'raw_binding_json':json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False)});return
                raise RuntimeError('original accepted malformed lifecycle case: '+name)
            for key in ordinary:
                bad=copy.deepcopy(ordinary);bad.pop(key);reject('missing_'+key,bad)
            reject('unknown_field',{**ordinary,'qualified':True})
            reject('ordinary_missing_environment',{**ordinary,'environment_sha256':None})
            reject('uppercase_digest',{**ordinary,'environment_sha256':'A'*64})
            reject('wrong_lifecycle',{**ordinary,'lifecycle':'ordinary'})
            reject('off_rogue_mismatch',{**legacy(),'xar_enabled':'xar_off'})
            reject('unknown_claims_off',{**unknown(),'xar_enabled':'xar_off'})
            reject('absence_wrong_source',{**absent,'source':'prepared-environment-manifest'})
            reject('boolean_source',{**ordinary,'source':True})
            reject('boolean_setting',{**ordinary,'xar_enabled':False})
            reject('empty_source',{**ordinary,'source':''})
            mixed=payload(ordinary);mixed['last_checkpoint']['succession_lifecycle']['environment_sha256']='e'*64
            if consumer(_checkpoint_binding,mixed)['accepted']:raise RuntimeError('actual consumer accepted mixed anchors')
            anchor_cases=[]
            def anchors(value):return [copy.deepcopy(value['succession_lifecycle']),copy.deepcopy(value['last_checkpoint']['succession_lifecycle']),copy.deepcopy(value['command_history'][0]['result']['checkpoint']['succession_lifecycle'])]
            def anchor_case(name,value):
                outcomes={'checkpoint_environment_binding':consumer(_checkpoint_binding,value),'ordinary_seed_anchors':consumer(lambda v:ordinary_anchors(v)[-1],value),'rogue_checkpoint_anchors':consumer(lambda v:rogue_anchors(v)[-1],value)}
                anchor_cases.append({'name':name,'anchors':anchors(value),'actual_consumers':outcomes})
            for profile,binding in [('ordinary',ordinary),('rogue',{**legacy(),'source':'prepared-environment-manifest','environment_sha256':'b'*64})]:
                anchor_case(profile+'_equal_anchors',payload(binding))
                for ordinal in range(3):
                    for mutation in ('source_drift','environment_drift','missing'):
                        value=payload(binding);containers=[value,value['last_checkpoint'],value['command_history'][0]['result']['checkpoint']]
                        if mutation=='missing':containers[ordinal]['succession_lifecycle']=None
                        else:containers[ordinal]['succession_lifecycle']['source' if mutation=='source_drift' else 'environment_sha256']='different-original-source' if mutation=='source_drift' else 'f'*64
                        anchor_case(profile+'_'+str(ordinal)+'_'+mutation,value)
            after=refs()
            if before!=after:raise RuntimeError('original source changed during capture')
            machine=subprocess.run([sys.executable,str(root/'tools/ck3_live_run_id.py'),'machine'],check=True,capture_output=True,text=True).stdout.strip()
            print(json.dumps({'schema':'xar.java-succession-lifecycle-original-golden/v1','machine_id':machine,'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Offline full four original unittest modules over synthetic temporary fixture files, constructors/normalizer, and complete checkpoint/ordinary/rogue three-anchor readers. Original filesystem/environment/SAVE validation runs only against synthetic fixtures; no live SAVE, Game, SDK continuation or canonical writer authority.','source_refs':before,'source_refs_unchanged':True,'original_unittest':{'whole_modules':True,'modules':unit_paths,'discovered_tests':len(ids),'discovered_test_ids':ids,'tests':unit_result.testsRun,'failures':len(unit_result.failures),'errors':len(unit_result.errors),'skipped':len(unit_result.skipped)},'cases':cases,'rejections':invalid,'anchor_consumer_cases':anchor_cases,'actual_checkpoint_consumer_rejected_mixed_anchors':True},ensure_ascii=False,separators=(',',':'),allow_nan=False))
            """;
}
