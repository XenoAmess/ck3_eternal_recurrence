package org.xar.ck3.control.wave2.military.warresults;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Once-only old-producer capture. The ordinary Java tests never launch Python. */
public final class WarResultsGoldenCapture {
    private WarResultsGoldenCapture() { }
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 4) { throw new IllegalArgumentException("repository python-exe fresh-output machine-id required"); }
        Path repository = Path.of(args[0]).toAbsolutePath().normalize(); Path output = Path.of(args[2]).toAbsolutePath().normalize();
        if (Files.exists(output)) { throw new IllegalArgumentException("fresh capture output required"); }
        ProcessBuilder builder = new ProcessBuilder(List.of(args[1], "-B", "-X", "utf8", "-c", PROGRAM, repository.toString(), args[3]));
        builder.directory(repository.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1");
        builder.environment().put("PYTHONPATH", repository + File.pathSeparator + repository.resolve("ck3_autonomous_player/src")
                + File.pathSeparator + repository.resolve("ck3_autonomous_player/tests/unit"));
        builder.redirectError(ProcessBuilder.Redirect.INHERIT); Process process = builder.start(); byte[] bytes;
        try (var reader = Executors.newSingleThreadExecutor()) {
            var response = reader.submit(() -> { try (var stream = process.getInputStream()) { return stream.readNBytes(65_537); } });
            if (!process.waitFor(90, TimeUnit.SECONDS)) {
                process.descendants().forEach(ProcessHandle::destroyForcibly); process.destroyForcibly(); throw new IOException("producer capture timeout");
            }
            try { bytes = response.get(); } catch (ExecutionException error) { throw new IOException("capture read failed", error.getCause()); }
        }
        if (process.exitValue() != 0 || bytes.length == 0 || bytes.length > 65_536) { throw new IOException("capture failed/over budget: exit=" + process.exitValue() + " bytes=" + bytes.length); }
        Files.createDirectories(output.getParent()); Files.write(output, bytes, StandardOpenOption.CREATE_NEW);
        System.out.println("captured " + bytes.length + " bytes to " + output);
    }

    private static final String PROGRAM = """
            import sys,json,copy,hashlib,datetime,contextlib
            from pathlib import Path
            import pytest
            from xar_autoplayer import ordinary_war_results_window_v1 as p
            root=Path(sys.argv[1]); machine=sys.argv[2]
            test_paths=['ck3_autonomous_player/tests/unit/test_war_results_window_priority.py','ck3_autonomous_player/tests/unit/test_war_results_scope_connection.py']
            reports=[]
            class Reports:
                def pytest_runtest_logreport(self,report): reports.append(report)
            with contextlib.redirect_stdout(sys.stderr):
                code=pytest.main(['-q','-p','no:cacheprovider',*test_paths],plugins=[Reports()])
            calls=[r for r in reports if r.when=='call']
            if code != 0 or len(calls)!=4 or not all(r.passed for r in calls) or any(r.skipped for r in reports): raise RuntimeError('original four priority/connection tests failed or skipped')
            def frame():
                return dict(snapshot_id='native:9',revision=3,native_revision=9,date_raw=53100000,episode_run_id='robert',paused=True,map_ready=True,played_character={'character_id':31254,'alive':True},diagnostics={'connection_generation':3})
            def source(s,**kw): return dict(sdk_validation_schema=p.SOURCE_SCHEMA if hasattr(p,'SOURCE_SCHEMA') else 'war-results-window-source-v1',**p._binding(s),available=True,post_observed=True,scope_unchanged=True,post_window_present=True,post_effective_visible=True,**kw)
            def attempt(s,status='failed'): return dict(validation_schema='war-results-window-query-attempt-v1',**p._binding(s),status=status,native_request_id='read-original')
            def packet(s=None): return dict(schema='xar.ck3.war-results-priority-input/v1',snapshot=frame() if s is None else s,action_steps=[p.QUERY_WAR_RESULTS_WINDOW_V1_STEP,p.CLOSE_WAR_RESULTS_WINDOW_V1_STEP,'pause-map'],bridge_capabilities=[p.QUERY_WAR_RESULTS_WINDOW_V1_CAPABILITY,p.CLOSE_WAR_RESULTS_WINDOW_V1_CAPABILITY])
            cases=[]
            def put(name,x):
                s=x['snapshot']; o=s.get('war_results_window_v1_observation') if isinstance(s,dict) else None
                cases.append(dict(name=name,input=x,plan=p.plan_ordinary_war_results_window_v1(s,action_steps=x['action_steps'],bridge_capabilities=x['bridge_capabilities']),presence=p.war_results_window_presence_v1(o),query_frame=list(p.war_results_window_query_frame_v1(s)) if isinstance(s,dict) else None))
            x=packet(); x['snapshot']=None; put('null-snapshot',x)
            x=packet(); x['bridge_capabilities']=[]; put('no-capabilities',x)
            put('unknown-query',packet())
            x=packet(); x['action_steps']=[]; put('missing-steps-blocked',x)
            x=packet(); x['bridge_capabilities']=[p.CLOSE_WAR_RESULTS_WINDOW_V1_CAPABILITY]; put('close-only-unknown',x)
            for name,flags in [('absent',dict(post_window_present=False,post_effective_visible=False)),('hidden',dict(post_effective_visible=False)),('visible',{}),('unobserved',dict(post_observed=False)),('scope-changed',dict(scope_unchanged=False)),('unavailable',dict(available=False)),('inconsistent-visible',dict(post_window_present=False)),('ack-only',dict(post_observed=False,accepted=True,dispatch_attempted=True,dispatch_invoked=True))]:
                x=packet(); s=x['snapshot']; o=source(s); o.update(flags); s['war_results_window_v1_observation']=o; put(name,x)
            x=packet(); s=x['snapshot']; s['war_results_window_v1_observation']=source(s); x['bridge_capabilities']=[p.QUERY_WAR_RESULTS_WINDOW_V1_CAPABILITY]; put('visible-close-unavailable',x)
            x=packet(); s=x['snapshot']; s['war_results_window_v1_observation']=source(s,close_retry_deferred_for_native_frame=True); put('visible-retry-deferred',x)
            for name,value in [('check-not-due',False),('check-null',None),('check-due',True)]:
                x=packet(); x['snapshot']['war_results_window_v1_check_due']=value; put(name,x)
            for name,status in [('failed-read-current','failed'),('attempt-current','submitted')]:
                x=packet(); s=x['snapshot']; s['war_results_window_v1_query_attempt']=attempt(s,status); put(name,x)
            x=packet(); s=x['snapshot']; s['war_results_window_v1_query_attempt']=attempt(s); s['revision']+=1; put('stale-failed-attempt',x)
            for name,field in [('stale-public-revision','queried_revision'),('stale-native-revision','queried_native_revision'),('stale-date','queried_date_raw'),('stale-actor','queried_actor_character_id'),('stale-connection','queried_connection_generation')]:
                x=packet(); s=x['snapshot']; o=source(s); o[field]+=1; s['war_results_window_v1_observation']=o; put(name,x)
            x=packet(); s=x['snapshot']; o=source(s); o['sdk_validation_schema']='other'; s['war_results_window_v1_observation']=o; put('wrong-source-marker',x)
            x=packet(); s=x['snapshot']; s['war_results_window_v1_observation']=source(s); s['war_results_window_v1_close_pending']={'native_request_id':'original-close'}; put('pending-visible-observe-once',x)
            x=copy.deepcopy(x); x['snapshot']['war_results_window_v1_query_attempt']=attempt(x['snapshot']); put('pending-visible-never-resubmit',x)
            x=packet(); s=x['snapshot']; s['war_results_window_v1_close_pending']={}; s['war_results_window_v1_check_due']=False; put('empty-pending-object-stays-pending',x)
            x=packet(); s=x['snapshot']; s['war_results_window_v1_observation']=source(s); s['war_results_window_v1_observation']['post_effective_visible']=False; s['war_results_window_v1_close_pending']={'native_request_id':'unresolved'}; put('hidden-with-unresolved-close',x)
            for name,field,value in [('map-not-ready','map_ready',False),('unpaused-pause-first','paused',False),('pause-unknown','paused',None)]:
                x=packet(); x['snapshot'][field]=value; put(name,x)
            x=packet(); x['snapshot']['paused']=False; x['action_steps'].remove('pause-map'); put('unpaused-no-pause-capability',x)
            x=packet(); s=x['snapshot']; s['war_results_window_v1_query_attempt']=dict(status='foreign-attempt'); s['war_results_window_v1_next_check_date_raw']=53100144; put('unbound-attempt-status-projection',x)
            x=packet(); x['snapshot'].pop('snapshot_id'); x['snapshot'].pop('revision'); put('missing-public-binding',x)
            x=packet(); s=x['snapshot']; s['snapshot_id']=None; s['revision']=None; o=source(s); o['queried_snapshot_id']=None; o['queried_revision']=None; s['war_results_window_v1_observation']=o; put('null-binding-explicit-match',x)
            paths=['ck3_autonomous_player/src/xar_autoplayer/ordinary_war_results_window_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/war_results_window_transport.py','ck3_autonomous_player/src/xar_autoplayer/bridge/war_results_window_contract.py',*test_paths]
            pins=[dict(path=p,sha256=hashlib.sha256((root/p).read_bytes()).hexdigest()) for p in paths]
            output=dict(schema='xar.ck3.war-results-priority-golden/v1',machine_id=machine,captured_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_machine_id='unknown',original_tests=len(calls),original_skipped=0,source_pins=pins,cases=cases)
            raw=json.dumps(output,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
            if len(raw)>65536: raise RuntimeError('golden exceeds 64KiB budget')
            sys.stdout.buffer.write(raw)
            """;
}
