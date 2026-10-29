package org.xar.ck3.control.wave2.military.wardeclaredoverview;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Once-only real producer capture over the committed shared input scenarios. */
public final class WarDeclaredOverviewGoldenCapture {
    private WarDeclaredOverviewGoldenCapture() { }
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
            from xar_autoplayer import ordinary_war_declared_overview_v1 as p
            root=Path(sys.argv[1]); machine=sys.argv[2]
            corpus_path='java/ck3-control/wave2-military/src/test/resources/warresults/producer-golden.json'
            corpus_raw=(root/corpus_path).read_bytes(); corpus=json.loads(corpus_raw)
            test_paths=['ck3_autonomous_player/tests/unit/test_war_declared_overview_priority.py','ck3_autonomous_player/tests/unit/test_war_declared_overview_latch_reconciliation.py']
            reports=[]
            class Reports:
                def pytest_runtest_logreport(self,report): reports.append(report)
            with contextlib.redirect_stdout(sys.stderr):
                code=pytest.main(['-q','-p','no:cacheprovider',*test_paths],plugins=[Reports()])
            calls=[r for r in reports if r.when=='call']
            if code != 0 or len(calls)!=15 or not all(r.passed for r in calls) or any(r.skipped for r in reports): raise RuntimeError('original fifteen priority/latch tests failed or skipped')
            steps={'query-war-results-window-v1':'query-war-declared-overview-v1','close-war-results-window-v1':'close-war-declared-overview-v1'}
            caps={'game.command.'+k:'game.command.'+v for k,v in steps.items()}
            keys={'war_results_window_v1_observation':'war_declared_overview_v1_observation','war_results_window_v1_query_attempt':'war_declared_overview_v1_query_attempt','war_results_window_v1_close_pending':'war_declared_overview_v1_close_pending'}
            cases=[]
            for old in corpus['cases']:
                inp=copy.deepcopy(old['input']); inp['schema']='xar.ck3.war-declared-overview-priority-input/v1'
                inp['action_steps']=[steps.get(v,v) for v in inp['action_steps']]; inp['bridge_capabilities']=[caps.get(v,v) for v in inp['bridge_capabilities']]
                s=inp['snapshot']
                if isinstance(s,dict):
                    for before,after in keys.items():
                        if before in s: s[after]=s.pop(before)
                    o=s.get('war_declared_overview_v1_observation')
                    if isinstance(o,dict) and o.get('sdk_validation_schema')=='war-results-window-source-v1': o['sdk_validation_schema']='war-declared-overview-source-v1'
                    a=s.get('war_declared_overview_v1_query_attempt')
                    if isinstance(a,dict) and a.get('validation_schema')=='war-results-window-query-attempt-v1': a['validation_schema']='war-declared-overview-query-attempt-v1'
                observation=s.get('war_declared_overview_v1_observation') if isinstance(s,dict) else None
                cases.append(dict(name=old['name'],input=inp,plan=p.plan_ordinary_war_declared_overview_v1(s,action_steps=inp['action_steps'],bridge_capabilities=inp['bridge_capabilities']),presence=p.war_declared_overview_presence_v1(observation),query_frame=list(p.war_declared_overview_query_frame_v1(s)) if isinstance(s,dict) else None))
            paths=['ck3_autonomous_player/src/xar_autoplayer/ordinary_war_declared_overview_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/war_declared_overview_contract.py','ck3_autonomous_player/src/xar_autoplayer/bridge/war_declared_overview_transport.py',*test_paths]
            pins=[dict(path=p,sha256=hashlib.sha256((root/p).read_bytes()).hexdigest()) for p in paths]
            output=dict(schema='xar.ck3.war-declared-overview-priority-golden/v1',machine_id=machine,captured_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_machine_id='unknown',original_tests=len(calls),original_skipped=0,source_pins=pins,input_corpus_ref=dict(path=corpus_path,bytes=len(corpus_raw),sha256=hashlib.sha256(corpus_raw).hexdigest()),cases=cases)
            raw=json.dumps(output,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
            if len(raw)>65536: raise RuntimeError('golden exceeds 64KiB budget')
            sys.stdout.buffer.write(raw)
            """;
}
