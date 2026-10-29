package org.xar.ck3.control.g2.m0.integration;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Software-only integration: original producers and consumers use a real compiled Java evaluator.
 * This test entry has no game, save-state, action-submission or live-admission API.
 */
public final class M0ConsumerRoundTrip {
    public static final String DOMAIN_MAIN = "org.xar.ck3.control.g2.m0.integration.M0UnionStdioAdapter";
    private static final Duration DEADLINE = Duration.ofSeconds(150);
    private static final int SOURCE_MAXIMUM_BYTES = 1_048_576;
    private M0ConsumerRoundTrip() { }

    /** Run only beneath the shared bounded Job owner; its complete classpath is supplied by that owner. */
    public static void main(String[] args) throws IOException, InterruptedException {
        run(args, DOMAIN_MAIN);
    }

    public static void run(String[] args, String domainMain) throws IOException, InterruptedException {
        run(args, domainMain, null);
    }

    public static void run(String[] args, String domainMain, Path transportConfig) throws IOException, InterruptedException {
        if (!DOMAIN_MAIN.equals(domainMain)
                && !"org.xar.ck3.control.g2.m0.integration.M0HttpStdioAdapter".equals(domainMain)) {
            throw new IllegalArgumentException("one declared M0 test transport required");
        }
        if (args.length != 7) {
            throw new IllegalArgumentException("repository, python, java, compiled-classpath, fresh-output, original-recommendation-sha256, fresh-test-scratch required");
        }
        M0FixtureConfig staticConfig = M0FixtureConfig.fromEnvironment();
        Path repository = Path.of(args[0]).toRealPath();
        Path python = Path.of(args[1]).toRealPath();
        Path javaExecutable = Path.of(args[2]).toRealPath();
        Path output = Path.of(args[4]).toAbsolutePath().normalize();
        Path testScratch = Path.of(args[6]).toAbsolutePath().normalize();
        if (Files.exists(output) || !Files.isDirectory(output.getParent())
                || Files.exists(testScratch) || !Files.isDirectory(testScratch.getParent())
                || !args[5].matches("[0-9a-f]{64}")) {
            throw new IllegalArgumentException("fresh admitted output and actual source SHA-256 required");
        }
        Path source = Path.of(staticConfig.recommendationOracle().path());
        byte[] original = readSource(source);
        if (!sha256(original).equals(args[5])) throw new IllegalArgumentException("original recommendation source drifted");
        Path body = output.resolveSibling(output.getFileName() + ".body.py");
        Files.writeString(body, SCRIPT, StandardCharsets.UTF_8, StandardOpenOption.CREATE_NEW);
        List<String> command = new ArrayList<>(List.of(python.toString(), "-B", "-X", "utf8", body.toString(),
                repository.toString(), javaExecutable.toString(), args[3], domainMain, output.toString(), args[5],
                staticConfig.recommendationAdapter().path(), staticConfig.formalAdapter().path(), staticConfig.clientAdapter().path(), staticConfig.recommendationOracle().path()));
        ProcessBuilder builder = new ProcessBuilder(command).directory(repository.toFile()).inheritIO();
        Files.createDirectory(testScratch);
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("TMP", testScratch.toString());
        builder.environment().put("TEMP", testScratch.toString());
        builder.environment().put("TMPDIR", testScratch.toString());
        builder.environment().put("XAR_G2_M0_HTTP_CALL_EVIDENCE", output.resolveSibling(output.getFileName() + ".http-calls.json").toString());
        if (transportConfig != null) builder.environment().put("XAR_G2_M0_FIXTURE_CONFIG", transportConfig.toString());
        builder.environment().put("PYTHONPATH", repository.toString() + java.io.File.pathSeparator + repository.resolve("ck3_autonomous_player/src")
                + java.io.File.pathSeparator + repository.resolve("ck3_workshop_mcp/src")
                + java.io.File.pathSeparator + repository.resolve("ck3_autonomous_player/tests/unit"));
        Process child = builder.start();
        if (!child.waitFor(DEADLINE.toMillis(), TimeUnit.MILLISECONDS)) {
            child.descendants().forEach(ProcessHandle::destroyForcibly);
            child.destroyForcibly();
            throw new IllegalStateException("M0 software consumer timeout; shared Job owner retains terminal accounting");
        }
        if (!java.util.Arrays.equals(original, readSource(source))) throw new IllegalStateException("original source changed during consumer tests");
        if (child.exitValue() != 0) throw new IllegalStateException("M0 original consumer integration RED, actual exit " + child.exitValue());
        if (!Files.isRegularFile(output) || Files.size(output) == 0 || Files.size(output) > 262_144) {
            throw new IllegalStateException("finite software consumer receipt missing or oversized");
        }
    }

    private static byte[] readSource(Path source) throws IOException {
        try (var stream = Files.newInputStream(source)) {
            byte[] raw = stream.readNBytes(SOURCE_MAXIMUM_BYTES + 1);
            if (raw.length > SOURCE_MAXIMUM_BYTES) throw new IllegalArgumentException("finite direct source required");
            return raw;
        }
    }
    private static String sha256(byte[] value) {
        try { return java.util.HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }

    private static final String SCRIPT = """
            import sys, os, json, hashlib, datetime, subprocess, importlib, importlib.util, unittest, traceback
            from pathlib import Path
            repo, java, classpath, domain_main, output, expected_source_sha, adapter_path, formal_path, client_path, oracle_path = sys.argv[1:]
            repo=Path(repo); output=Path(output); adapter_path=Path(adapter_path); formal_path=Path(formal_path); client_path=Path(client_path)
            if output.exists(): raise ValueError('fresh admitted output required')
            source=Path(oracle_path)
            source_bytes=source.read_bytes()
            if hashlib.sha256(source_bytes).hexdigest()!=expected_source_sha: raise ValueError('recommendation source drift')
            names=(
                'test_raiktor_three_way_exit_recommendation',
                'test_raiktor_three_way_exit_action_gate',
                'test_raiktor_formal_exit_consumer',
                'test_raiktor_three_way_exit_postcondition',
                'test_raiktor_three_way_exit_postwar_evidence',
                'test_raiktor_checkpoint_replay_recommendation_provider',
                'test_gen034_three_way_recommendation_live_acceptance',
                'test_gen034_three_way_exit_action_live_acceptance',
                'test_prepare_g2_three_way_exit_file_intake',
                'test_raiktor_exit_utility_evaluator',
            )
            unit=repo/'ck3_autonomous_player/tests/unit'
            body=Path(__file__).resolve()
            pinned={str(source):source_bytes,str(body):body.read_bytes()}
            for path in (adapter_path, formal_path, client_path): pinned[str(path)]=path.read_bytes()
            for name in names:
                path=unit/(name+'.py'); pinned[str(path)]=path.read_bytes()
            child=None
            calls=0; replies=0; roundtrips=0; rejection_count=0; trace_count=0
            operation_counts={}; formal_actual_calls=0; checking_trace=False; oracle_comparisons=0; oracle_rejections=0
            request_hashes=set(); reply_hashes=set()
            def canonical(value):
                return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
            def java_evaluate(payload):
                global child,calls,replies,roundtrips,rejection_count
                line=canonical(payload)
                if len(line.encode('utf-8'))>1048576: raise ValueError('finite Java semantic request required')
                if child is None:
                    child=subprocess.Popen([java,'-Xms8m','-Xmx32m','-XX:+UseSerialGC','-XX:ActiveProcessorCount=2',
                        '-XX:MaxMetaspaceSize=64m','-XX:ReservedCodeCacheSize=16m','-XX:MaxDirectMemorySize=8m','-Xss256k','-cp',classpath,domain_main,'--stdio'],
                        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=sys.stderr,text=True,encoding='utf-8',bufsize=1)
                operation=payload.get('operation','')
                operation_counts[operation]=operation_counts.get(operation,0)+1
                calls+=1; request_hashes.add(hashlib.sha256(line.encode('utf-8')).hexdigest())
                child.stdin.write(line+'\\n'); child.stdin.flush()
                raw=child.stdout.readline(1048577)
                if not raw or not raw.endswith('\\n') or len(raw.encode('utf-8'))>1048576:
                    raise RuntimeError('compiled Java evaluator response unavailable or oversized')
                reply=json.loads(raw); replies+=1
                if isinstance(reply,dict) and reply.get('rejected') is True:
                    if set(reply)!={'rejected','message'} or not isinstance(reply['message'],str):
                        raise RuntimeError('compiled rejection shape drifted')
                    rejection_count+=1
                    raise recommendation.ThreeWayExitRecommendationError(reply['message'])
                if not isinstance(reply,dict):
                    raise RuntimeError('compiled Java response contract drifted')
                persisted=json.loads(canonical(reply))
                if persisted!=reply: raise AssertionError('Java response JSON persistence drift')
                roundtrips+=1; reply_hashes.add(hashlib.sha256(canonical(reply).encode('utf-8')).hexdigest())
                return persisted
            def load_static(name,path):
                spec=importlib.util.spec_from_file_location(name,path)
                module=importlib.util.module_from_spec(spec)
                sys.modules[name]=module
                spec.loader.exec_module(module)
                return module
            import tools.g2_saved_campaign
            load_static('tools.g2_saved_campaign.java_map_admission_client_v1',client_path)
            import xar_autoplayer.simulation
            recommendation=load_static('xar_autoplayer.simulation.raiktor_three_way_exit_recommendation',adapter_path)
            recommendation._invoke_java_m0=java_evaluate
            oracle=load_static('m0_original_recommendation_oracle',source)
            setattr(xar_autoplayer.simulation,'raiktor_three_way_exit_recommendation',recommendation)
            import xar_autoplayer
            formal=load_static('xar_autoplayer.raiktor_formal_exit',formal_path)
            setattr(xar_autoplayer,'raiktor_formal_exit',formal)
            formal_trace=formal._utility_comparison_trace
            def record_formal_trace(certificate):
                global formal_actual_calls
                if not checking_trace:formal_actual_calls+=1
                return formal_trace(certificate)
            formal._utility_comparison_trace=record_formal_trace
            provide=recommendation.provide_raiktor_three_way_exit_recommendation
            def verify_rendered(*args,**kwargs):
                global trace_count,checking_trace,oracle_comparisons,oracle_rejections
                expected_error=None
                try:expected=oracle.provide_raiktor_three_way_exit_recommendation(*args,**kwargs)
                except (KeyError,TypeError,ValueError) as error:expected_error=error
                try:result=provide(*args,**kwargs)
                except (KeyError,TypeError,ValueError):
                    if expected_error is None:raise AssertionError('static Java adapter rejected accepted original producer input')
                    oracle_rejections+=1
                    raise
                if expected_error is not None:raise AssertionError('static Java adapter accepted rejected original producer input')
                if canonical(result)!=canonical(expected):raise AssertionError('full static Java recommendation receipt differs from actual original producer')
                oracle_comparisons+=1
                if json.loads(canonical(result))!=result: raise AssertionError('recommendation persisted JSON representation drift')
                certificate=result.get('recommendation_certificate')
                if certificate is not None:
                    unhashed={k:v for k,v in certificate.items() if k!='certificate_sha256'}
                    digest=hashlib.sha256(canonical(unhashed).encode('utf-8')).hexdigest().upper()
                    if digest!=certificate['certificate_sha256']: raise AssertionError('Java decision broke original certificate hash')
                    from xar_autoplayer.raiktor_formal_exit import _utility_comparison_trace
                    checking_trace=True
                    try:trace=_utility_comparison_trace(certificate)
                    finally:checking_trace=False
                    if json.loads(canonical(trace))!=trace: raise AssertionError('formal trace JSON representation drift')
                    if result.get('postcondition_verified') is not False or result.get('gen034_closed') is not False:
                        raise AssertionError('software evaluation fabricated game completion')
                    trace_count+=1
                return result
            recommendation.provide_raiktor_three_way_exit_recommendation=verify_rendered
            formal.provide_raiktor_three_way_exit_recommendation=verify_rendered
            suite=unittest.TestSuite()
            module_counts=[]
            result=None; terminal_exit=None; integration_error=None
            try:
                for name in names:
                    module=importlib.import_module(name)
                    if Path(module.__file__).resolve()!=unit/(name+'.py'): raise ValueError('original consumer origin drift')
                    selected=unittest.defaultTestLoader.loadTestsFromModule(module)
                    module_counts.append({'module':name,'tests':selected.countTestCases()})
                    suite.addTests(selected)
                result=unittest.TextTestRunner(stream=sys.stderr,verbosity=2).run(suite)
            except BaseException:
                integration_error=traceback.format_exc()
            finally:
                if child is not None:
                    try: child.stdin.close()
                    except (BrokenPipeError,OSError) as error:
                        integration_error=(integration_error or '')+'\\ncompiled Java input close failed: '+str(error)
                    try: terminal_exit=child.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        child.kill(); terminal_exit=child.wait(timeout=15)
                        integration_error=(integration_error or '')+'\\ncompiled Java evaluator failed finite close'
            changed=[path for path,raw in pinned.items() if Path(path).read_bytes()!=raw]
            actual_http=False; http_evidence=None
            if domain_main.endswith('.M0HttpStdioAdapter'):
                http_path=Path(os.environ['XAR_G2_M0_HTTP_CALL_EVIDENCE'])
                if http_path.is_file():
                    http_raw=http_path.read_bytes()
                    if len(http_raw)>131072: raise ValueError('finite HTTP call evidence exceeded')
                    http_evidence=json.loads(http_raw)
                    actual_http=(http_evidence.get('actual_http') is True and http_evidence.get('calls')==calls
                        and http_evidence.get('verified_responses')==replies and http_evidence.get('unknown')==0)
                if not actual_http: integration_error=(integration_error or '')+'\\nactual shared-client HTTP evidence missing or incomplete'
            tests=0 if result is None else result.testsRun
            skipped=[] if result is None else [(str(test),reason) for test,reason in result.skipped]
            failures=[] if result is None else [(str(test),detail) for test,detail in result.failures]
            errors=[] if result is None else [(str(test),detail) for test,detail in result.errors]
            success=(result is not None and result.wasSuccessful() and not skipped and not changed
                and calls>0 and calls==replies and roundtrips>0 and trace_count>0 and formal_actual_calls>0 and terminal_exit==0 and integration_error is None)
            observed_machine=subprocess.check_output([sys.executable,'-B',str(repo/'tools/ck3_live_run_id.py'),'machine'],text=True).strip()
            receipt={
                'schema':'xar.g2-m0-consumer-roundtrip/v1','machine_id':observed_machine,
                'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'status':'PASS' if success else 'RED','scope':'software_only_original_producer_compiled_java_decision_original_consumers',
                'domain_main':domain_main,'class_path':classpath,'transport':'real_compiled_java_ndjson_no_oracle_lookup',
                'source_overlay':'static_existing_module_thin_adapters_no_source_splice_java_composer_and_trace',
                'source_overlay_sha256':hashlib.sha256(pinned[str(adapter_path)]).hexdigest(),
                'source_overlay_ref':{'path':str(adapter_path),'bytes':len(pinned[str(adapter_path)]),'sha256':hashlib.sha256(pinned[str(adapter_path)]).hexdigest()},
                'direct_source_refs':[{'path':path,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for path,raw in pinned.items()],
                'direct_source_changed':changed,'full_modules':module_counts,'tests':tests,
                'skipped':skipped,'failures':failures,'errors':errors,'integration_error':integration_error,
                'actual_domain_calls':calls,'actual_domain_replies':replies,'domain_rejections':rejection_count,
                'actual_operation_counts':operation_counts,'actual_formal_planner_trace_calls':formal_actual_calls,
                'actual_original_full_receipt_comparisons':oracle_comparisons,'actual_original_rejection_comparisons':oracle_rejections,
                'java_json_roundtrips':roundtrips,'original_certificate_and_formal_trace_roundtrips':trace_count,
                'unique_request_sha256':sorted(request_hashes),'unique_response_sha256':sorted(reply_hashes),
                'domain_process_exit':terminal_exit,
                'http_call_evidence':http_evidence,
                'qualification':{'upstream_all_normalizers_migrated':False,'actual_http':actual_http,'runtime_takeover':False,
                    'all_production_callers_migrated':False,
                    'legacy_consumer':'separate static existing-module adapter test required',
                    'game_calls':0,'actual_driver_state_reads':0,'actual_save_state_reads':0,'new_game_days':0,
                    'action_submitted':False,'postcondition_verified':False,'cold_restore_verified':False,'gen034_closed':False},
            }
            raw=(canonical(receipt)+'\\n').encode('utf-8')
            if len(raw)>262144: raise ValueError('finite consumer receipt exceeded; retain shared owner stderr')
            with output.open('xb') as stream: stream.write(raw)
            print(json.dumps({'status':receipt['status'],'tests':tests,'domain_calls':calls,'output_bytes':len(raw),'output_sha256':hashlib.sha256(raw).hexdigest()}))
            if not success: raise SystemExit(1)
            """;
}
