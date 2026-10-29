package org.xar.ck3.control.wave2.military.warresultssource;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Explicit retained-source/old-normalizer capture; default JUnit uses only its committed output. */
public final class WarResultsSourceGoldenCapture {
    private WarResultsSourceGoldenCapture() { }
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 4) { throw new IllegalArgumentException("repository python-exe fresh-output machine-id required"); }
        Path repository = Path.of(args[0]).toAbsolutePath().normalize(); Path output = Path.of(args[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) { throw new IllegalArgumentException("fresh capture output required"); }
        ProcessBuilder builder = new ProcessBuilder(List.of(args[1], "-B", "-X", "utf8", "-c", PROGRAM, repository.toString(), args[3]));
        builder.directory(repository.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONPATH", repository + File.pathSeparator + repository.resolve("ck3_autonomous_player/src")
                + File.pathSeparator + repository.resolve("ck3_autonomous_player/tests/unit"));
        builder.redirectError(ProcessBuilder.Redirect.INHERIT); Process process = builder.start(); byte[] bytes;
        try (var reader = Executors.newSingleThreadExecutor()) {
            var response = reader.submit(() -> { try (var stream = process.getInputStream()) { return stream.readNBytes(65_537); } });
            if (!process.waitFor(90, TimeUnit.SECONDS)) { process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); throw new IOException("capture timeout"); }
            try { bytes = response.get(); } catch (ExecutionException error) { throw new IOException("capture read failed", error.getCause()); }
        }
        if (process.exitValue() != 0 || bytes.length == 0 || bytes.length > 65_536) { throw new IOException("capture failed/over budget exit=" + process.exitValue() + " bytes=" + bytes.length); }
        Files.createDirectories(output.getParent()); Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
        System.out.println("captured " + bytes.length + " bytes to " + output);
    }

    private static final String PROGRAM = """
            import sys,json,copy,hashlib,datetime,unittest
            from pathlib import Path
            from xar_autoplayer.bridge import war_results_window_contract as c
            from xar_autoplayer import ordinary_war_results_window_v1 as p
            from test_war_results_close_latch_reconciliation import Tests
            root=Path(sys.argv[1]); machine=sys.argv[2]
            run=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
            if not run.wasSuccessful() or run.testsRun!=10 or run.skipped: raise RuntimeError('original ten source/latch tests failed or skipped')
            fixture_path='ck3_autonomous_player/tests/fixtures/p41_results_close_query_projection.json'
            fixture=json.loads((root/fixture_path).read_bytes()); cases=[]
            def base(seq='812'):
                z=fixture['rows'][seq]['result']
                return dict(schema='xar.ck3.war-results-native-source-input/v1',expected_request_id=z['native_request_id'],operation=z['operation'],binding={'actor_character_id':z['queried_actor_character_id'],'date_raw':z['queried_date_raw'],'native_revision':z['queried_native_revision']},native_generation=z['queried_connection_generation'],owner_receipt=copy.deepcopy(z['native_command_result'][c.OWNER_RECEIPT_KEY]),leaf={k:copy.deepcopy(z[k]) for k in c._B15_FIELDS})
            def source_snapshot(x,seq):
                z=fixture['rows'][seq]['result']
                return dict(snapshot_id=z['queried_snapshot_id'],revision=z['queried_revision'],native_revision=z['queried_native_revision'],date_raw=z['queried_date_raw'],episode_run_id=z['queried_episode_run_id'],paused=True,map_ready=True,played_character={'character_id':z['queried_actor_character_id']},diagnostics={'connection_generation':z['queried_connection_generation']})
            def put(name,x,seq='812'):
                row=dict(name=name)
                if any(type(x['leaf'].get(k)) is float for k in ['native_revision']): row['input_raw']=json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
                else: row['input']=x
                try:
                    owner=c.normalize_war_results_window_owner_receipt_v1(x['owner_receipt'],request_id=x['expected_request_id'])
                    normalized=c.normalize_war_results_window_v1(x['leaf'],operation=x['operation'],binding=x['binding'],native_generation=x['native_generation'],owner_receipt=owner)
                except ValueError:
                    row['accepted']=False
                else:
                    row['accepted']=True; row['normalized']=normalized
                    s=source_snapshot(x,seq); row['consumer_snapshot']=copy.deepcopy(s)
                    s['war_results_window_v1_observation']={**normalized,**p._binding(s), 'sdk_validation_schema':'war-results-window-source-v1'}
                    row['consumer_plan']=p.plan_ordinary_war_results_window_v1(s,action_steps=[p.QUERY_WAR_RESULTS_WINDOW_V1_STEP,p.CLOSE_WAR_RESULTS_WINDOW_V1_STEP,'pause-map'],bridge_capabilities=[p.QUERY_WAR_RESULTS_WINDOW_V1_CAPABILITY,p.CLOSE_WAR_RESULTS_WINDOW_V1_CAPABILITY])
                    row['consumer_presence']=p.war_results_window_presence_v1(s['war_results_window_v1_observation'])
                cases.append(row)
            for seq in ['812','814','816']: put('retained-'+seq,base(seq),seq)
            x=base('814'); x['leaf'].update(available=True,accepted=True,status='closed_verified',unavailable_reason='',closure_verified=True,post_effective_visible=False); put('synthetic-post-verified-close',x,'814')
            x=base(); x['leaf'].pop('dismiss_stage'); x['leaf'].pop('dismiss_exception_code'); put('legacy-shape-without-trace',x)
            x=base('814'); x['leaf'].update(dismiss_stage='callback_entered',dispatch_invoked=False,native_handled=False); put('callback-entered-remains-pending',x,'814')
            for name,where,key,value in [
                ('wrong-schema','leaf','schema','other'),('wrong-window','leaf','window_name','other'),('different-operation','root','operation','close'),
                ('wrong-build','leaf','executable_sha256','0'*64),('owner-request-mismatch','owner_receipt','request_id','other'),
                ('owner-sequence-mismatch','owner_receipt','completed_sequence',999),('owner-pump-mismatch','owner_receipt','pump_epoch',999),
                ('owner-thread-mismatch','owner_receipt','thread_id',999),('owner-date-mismatch','owner_receipt','date_raw',999),
                ('owner-generation-mismatch','owner_receipt','connection_generation',999),('before-revision-mismatch','binding','native_revision',999),
                ('before-actor-mismatch','binding','actor_character_id',999),('pause-unverified','leaf','paused',False),
                ('post-impossible','leaf','post_window_present',False),('scope-changed','leaf','scope_unchanged',False),
                ('invocation-without-attempt','leaf','dispatch_invoked',True),('bool-native-revision','leaf','native_revision',True),
                ('float-native-revision','leaf','native_revision',586.0)]:
                x=base(); (x if where=='root' else x[where])[key]=value; put(name,x)
            x=base(); x['leaf'].update(status='absent',window_present=False,effective_visible=False,post_window_present=False,post_effective_visible=False,root_observation_source='guarded_registered_top_level',post_observation_source='guarded_registered_top_level'); put('absence-without-complete-owner-tree',x)
            x=base(); x['leaf'].pop('available'); put('missing-required-flag',x)
            x=base(); x['leaf'].pop('dismiss_exception_code'); put('partial-trace',x)
            x=base('814'); x['leaf']['accepted']=True; put('pending-close-cannot-claim-accepted',x,'814')
            x=base('814'); x['leaf']['unavailable_reason']='\u00a0'; put('unicode-whitespace-is-not-a-reason',x,'814')
            paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/war_results_window_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','ck3_autonomous_player/src/xar_autoplayer/ordinary_war_results_window_v1.py','ck3_autonomous_player/tests/unit/test_war_results_close_latch_reconciliation.py',fixture_path]
            output=dict(schema='xar.ck3.war-results-native-source-golden/v1',machine_id=machine,captured_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_machine_id='unknown',original_tests=run.testsRun,original_skipped=0,source_pins=[dict(path=p,sha256=hashlib.sha256((root/p).read_bytes()).hexdigest()) for p in paths],cases=cases)
            raw=json.dumps(output,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
            if len(raw)>65536: raise RuntimeError('golden exceeds 64KiB budget')
            sys.stdout.buffer.write(raw)
            """;
}
