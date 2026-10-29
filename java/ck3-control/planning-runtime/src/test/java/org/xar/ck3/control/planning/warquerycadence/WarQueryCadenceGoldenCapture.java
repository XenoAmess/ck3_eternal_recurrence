package org.xar.ck3.control.planning.warquerycadence;

import java.io.IOException;
import java.io.File;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;

/** Explicit one-time compatibility capture. Default JUnit never executes Python. */
public final class WarQueryCadenceGoldenCapture {
    private WarQueryCadenceGoldenCapture() { }

    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 4) { throw new IllegalArgumentException("repository python-exe output-json machine-id required"); }
        Path repository = Path.of(args[0]).toAbsolutePath().normalize();
        Path output = Path.of(args[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) { throw new IllegalArgumentException("capture must have a fresh output path"); }
        ProcessBuilder builder = new ProcessBuilder(List.of(args[1], "-B", "-X", "utf8", "-c", PYTHON_CAPTURE,
                repository.toString(), args[3]));
        builder.directory(repository.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONPATH", repository.resolve("ck3_autonomous_player/src") + File.pathSeparator
                + repository.resolve("ck3_autonomous_player/tests/unit"));
        builder.redirectError(ProcessBuilder.Redirect.INHERIT);
        Process process = builder.start(); byte[] bytes;
        try (var reader = Executors.newSingleThreadExecutor()) {
            var response = reader.submit(() -> {
                try (var stream = process.getInputStream()) { return stream.readNBytes(65_537); }
            });
            if (!process.waitFor(Duration.ofSeconds(60).toMillis(), TimeUnit.MILLISECONDS)) {
                process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly();
                throw new IOException("compatibility producer capture timed out");
            }
            try { bytes = response.get(); }
            catch (ExecutionException error) { throw new IOException("capture stdout could not be read", error.getCause()); }
        }
        if (process.exitValue() != 0 || bytes.length == 0 || bytes.length > 65_536) {
            throw new IOException("producer capture failed, exit=" + process.exitValue() + ", bytes=" + bytes.length);
        }
        Files.createDirectories(output.getParent()); Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
        System.out.println("captured " + bytes.length + " bytes to " + output);
    }

    private static final String PYTHON_CAPTURE = """
            import sys,json,hashlib,datetime,copy,unittest
            from pathlib import Path
            from test_war_termination_query_cadence_v1 import WarTerminationCadenceTest
            from xar_autoplayer.bridge.war_contract import war_termination_negative_query_signature as sig
            root=Path(sys.argv[1]); machine=sys.argv[2]
            suite=unittest.defaultTestLoader.loadTestsFromTestCase(WarTerminationCadenceTest)
            run=unittest.TextTestRunner(stream=sys.stderr,verbosity=1).run(suite)
            if not run.wasSuccessful() or run.testsRun != 7 or run.skipped: raise RuntimeError('original cadence tests failed')
            obj=WarTerminationCadenceTest(); obj.setUpClass()
            def base(warid=33554458): return obj.setup_case(warid)
            def root_input(case):
                s,ws,w,rs=case
                return dict(schema='xar.ck3.war-query-cadence-input/v1',snapshot=s,active_wars=ws,war=w,recent_records=rs)
            def canonical(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
            cases=[]
            def put(name,case):
                inp=root_input(case)
                cases.append(dict(name=name,input_sha256=hashlib.sha256(canonical(inp)).hexdigest(),expected=obj.eval(case)))
            put('actual-war-33554458',base()); put('actual-war-50331679',base(50331679))
            c=base(); c[3][:]=c[3][:1]; put('one-query',c)
            c=base(); d=copy.deepcopy(c[3][0]); d['result']['query_sequence']+=1; c[3][:]=[d,c[3][0]]; put('same-date-only',c)
            c=base(); c[0]['date_raw']=53222016+720; put('expiry-exact',c)
            c=base(); c[0]['date_raw']=53222016; put('same-current-date',c)
            c=base(); c[0]['date_raw']=53222016+719; put('before-expiry',c)
            c=base(); c[0]['date_raw']=53222016+720; d=copy.deepcopy(c[3][0]); d['result']['query_sequence']+=100; d['result']['termination_query_context']['queried_date_raw']=c[0]['date_raw']; c[0]['date_raw']+=168; c[3].insert(0,d); put('renewal',c)
            for name,key,value in [('actor-change','actor',999),('episode-change','episode','different'),('connection-change','connection',4),('terminal-score-positive','score',100),('terminal-score-negative','score',-100),('role-change','role',False),('new-war','new',999)]:
                c=base()
                if key=='actor': c[0]['played_character']['character_id']=value
                elif key=='episode': c[0]['episode_run_id']=value
                elif key=='connection': c[0]['diagnostics']['connection_generation']=value
                elif key=='score': c[2]['player_relative_war_score']=value
                elif key=='role': c[2]['player_is_primary_war_leader']=value
                else: c[1].append({**copy.deepcopy(c[2]),'war_id':value})
                put(name,c)
            for name,step in [('write-barrier','offer-white-peace-war-33554458'),('event-barrier','resolve-current-event'),('malformed-query','query-war-termination-options-033554458'),('restore-barrier','restore-checkpoint')]:
                c=base(); c[3].insert(0,dict(step=step,ok=True,result={})); put(name,c)
            c=base(); c[3].insert(0,dict(step='life-advance',ok=True,result={'war_action':{'status':'submitted'}})); put('action-barrier',c)
            c=base(); c[3][0]['ok']=False; put('failed-query',c)
            c=base(); c[0]['active_event']={'event_id':42}; put('active-event',c)
            c=base(); c[0]['pending_character_interaction']={'interaction_id':7}; put('pending-interaction',c)
            c=base(); c[0]['top_exclusive_modal_choice_hint']={'status':'present'}; put('exclusive-modal',c)
            for name,mutation in [('positive-peace-response','response'),('positive-autoaccept','auto'),('changed-cb','cb')]:
                c=base(); o=c[3][0]['result']['war_termination_options']
                if mutation=='response': o['options']['white_peace']['recipient_response']={'status':'available','would_accept_now':True,'decision_status_raw':1}
                elif mutation=='auto': o['options']['white_peace']['auto_accept_observable']=True; o['options']['white_peace']['auto_accept']=True
                else: o['active_casus_belli_identity']['database_index']=71
                c[3][0]['result']['termination_query_context']['negative_decision_signature']=sig(o); put(name,c)
            for name,key,days in [('claim-day-365','claim_cb',365),('dejure-day-180','individual_county_de_jure_cb',180)]:
                c=base(); c[2]['player_side']='attacker'
                for r in c[3]:
                    q=r['result']; o=q['war_termination_options']; ctx=q['termination_query_context']; o['player_side']='attacker'; o['player_is_primary_war_leader']=True
                    o['active_casus_belli_identity']={'database_index':70,'canonical_key':key}; o['cb_allows_white_peace']=True
                    o['war_duration_days']=days-5 if ctx['queried_date_raw']==53222016 else days-12
                    for w in ctx['active_war_signature']:
                        if w['war_id']==c[2]['war_id']: w['player_side']='attacker'
                    ctx['negative_decision_signature']=sig(o); ctx['queried_war_duration_days']=o['war_duration_days']
                c[0]['date_raw']=53222016+120; put(name,c)
                c[0]['date_raw']-=1; put(name+'-before',c)
            paths=['ck3_autonomous_player/src/xar_autoplayer/war_termination_query_cadence_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py','ck3_autonomous_player/tests/unit/test_war_termination_query_cadence_v1.py','ck3_autonomous_player/tests/unit/fixtures/termination_six_query_projection.json']
            pins=[dict(path=p,sha256=hashlib.sha256((root/p).read_bytes()).hexdigest()) for p in paths]
            result=dict(schema='xar.ck3.war-query-cadence-golden/v1',machine_id=machine,captured_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),original_test_count=run.testsRun,original_skipped=0,source_pins=pins,cases=cases)
            sys.stdout.buffer.write(canonical(result))
            """;
}
