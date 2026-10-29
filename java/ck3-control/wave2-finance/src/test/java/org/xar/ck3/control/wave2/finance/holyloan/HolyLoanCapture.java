package org.xar.ck3.control.wave2.finance.holyloan;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Explicit original-Python sampling only. Default JUnit consumes the committed compressed corpus. */
public final class HolyLoanCapture {
    private HolyLoanCapture() { }
    private static final String SCRIPT = """
        from copy import deepcopy
        from contextlib import redirect_stdout
        from datetime import datetime, timezone
        import gzip, hashlib, importlib, inspect, json
        from pathlib import Path
        import subprocess, sys
        repo=Path(sys.argv[1]).resolve(); machine=sys.argv[2]
        sys.path[:0]=[str(repo/'ck3_autonomous_player/src'),str(repo/'ck3_autonomous_player/tests/unit'),
            str(repo/'ck3_autonomous_player/tests'),str(repo/'tools'),str(repo)]
        import pytest
        from xar_autoplayer import holy_order_loan_decision_observation_v1 as loan
        from xar_autoplayer.bridge import war_cash_private_transport_v1 as cash
        from xar_autoplayer import war_mercenary_consumer_v1 as mercenary
        tests=['test_holy_order_loan_decision_observation_v1','test_war_cash_holy_order_loan_attach_v1',
            'test_war_cash_current_raw_context','test_g2_war_cash_net_income_wire',
            'test_war_cash_current_handoff_v1','test_campaign_score_existing_inputs_v1','test_episode04_ready_t0_12004']
        test_paths=['ck3_autonomous_player/tests/'+('' if p=='test_episode04_ready_t0_12004' else 'unit/')+p+'.py' for p in tests]
        sources=['ck3_autonomous_player/src/xar_autoplayer/'+p for p in (
            'holy_order_loan_decision_observation_v1.py','bridge/war_cash_private_transport_v1.py',
            'bridge/war_cash_current_raw_context_v1.py','bridge/war_payment_observations_v1.py',
            'bridge/version_identity.py','bridge/nonwar_private_build.py','war_mercenary_consumer_v1.py',
            'campaign_score_existing_inputs_v1.py','bridge/service.py','bridge/episode04_ready_t0_12004.py')]
        sources += test_paths + ['tools/ck3_mod_acceptance_cases/r10_common_arm.py']
        sources += ['ck3_autonomous_player/native_bridge/research/fixtures/ck3_12002_war_cash_current-resources-normal.json',
            'ck3_autonomous_player/tests/fixtures/construction_cash_current_12004.json']
        def pins():return {p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in sources}
        before=pins()
        modules=[importlib.import_module(p) for p in tests]
        originals={'project':loan.project_holy_order_loan_decision_observation_v1,
            'normalize':cash.normalize_war_cash_current_resources_v1,'monthly':cash._monthly_flow,
            'financing':mercenary._loan_financing_input}
        def encode(v):return json.dumps(v,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))
        probe=None
        if len(sys.argv)==5:
            probe=subprocess.Popen([sys.argv[3],'-Xms16m','-Xmx96m','-XX:MaxMetaspaceSize=64m','-cp',sys.argv[4],
                'org.xar.ck3.control.wave2.finance.holyloan.HolyLoanProbe'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=sys.stderr)
        vectors=[]; seen=set(); calls={p:0 for p in originals}; current=None; java_calls=0
        def java(raw):
            global java_calls
            probe.stdin.write(raw.encode('utf-8')+b'\\n');probe.stdin.flush()
            result=json.loads(probe.stdout.readline(65538));java_calls+=1;return result
        def wrap(name,fn):
            signature=inspect.signature(fn)
            def invoke(*args,**kwargs):
                calls[name]+=1
                arguments=deepcopy(dict(signature.bind(*args,**kwargs).arguments))
                raw=encode({'operation':name,'arguments':arguments})
                try: result=fn(*args,**kwargs)
                except (ValueError,TypeError,KeyError):
                    kind='invalid_contract';result=None
                    key=(raw,kind)
                    if key not in seen:seen.add(key);vectors.append((current,kind,raw,result))
                    if probe is not None and java(raw)!={'test_transport_status':'invalid_contract'}:
                        raise AssertionError('Java accepted invalid original '+name)
                    raise
                key=(raw,encode(result))
                if key not in seen:seen.add(key);vectors.append((current,'result',raw,deepcopy(result)))
                if probe is not None:
                    actual=java(raw)
                    if encode(actual)!=encode(result):raise AssertionError('Java mismatch '+name+' expected='+encode(result)[:700]+' actual='+encode(actual)[:700])
                    return actual
                return result
            return invoke
        replacements={p:wrap(p,fn) for p,fn in originals.items()}
        for module in list(sys.modules.values()):
            namespace=getattr(module,'__dict__',{})
            for key,fn in list(namespace.items()):
                for name,original in originals.items():
                    if fn is original:namespace[key]=replacements[name]
        class Plugin:
            def __init__(self):self.passed=0;self.skips=0;self.failures=0
            def pytest_runtest_setup(self,item):
                global current
                current=item.nodeid
            def pytest_runtest_logreport(self,report):
                if report.skipped:self.skips+=1
                if report.failed:self.failures+=1
                if report.when=='call' and report.passed:self.passed+=1
        plugin=Plugin()
        with redirect_stdout(sys.stderr):
            status=pytest.main(['-q','-p','no:cacheprovider',*test_paths],plugins=[plugin])
        if status or plugin.skips or plugin.failures or not plugin.passed or any(not n for n in calls.values()):
            raise SystemExit('original producer/consumer tests failed, skipped or missed an operation')
        if probe is not None:
            probe.stdin.close()
            if probe.wait(timeout=10)!=0:raise SystemExit('Java differential pipe failed')
        if pins()!=before:raise SystemExit('original source changed during capture')
        header={'schema':'xar.holyloan-rawcash-original-golden.v1','machine_id':machine,
            'observed_at_utc':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'source_sha256':before,
            'test_modules':tests,'passed':plugin.passed,'skips':plugin.skips,'calls':calls,'vector_count':len(vectors),
            'java_consumer_calls':java_calls,'native_game_rpc_count':0,'live_adoption':False,
            'scope':'original real functions via existing synthetic/retained-fixture tests; no native eligibility or money qualification'}
        lines=[encode(header).encode()]
        for ordinal,(test,kind,raw,result) in enumerate(vectors,1):
            expected=encode(result)
            if len(raw.encode())>65536 or len(expected.encode())>65536:raise SystemExit('vector exceeds declared wire bound')
            lines += [encode({'ordinal':ordinal,'test_case':test,'expected_kind':kind}).encode(),raw.encode(),expected.encode()]
        raw=b'\\n'.join(lines)+b'\\n'
        if len(raw)>4*1024*1024:raise SystemExit('raw corpus exceeds4MiB')
        packed=gzip.compress(raw,mtime=0)
        if len(packed)>65536:raise SystemExit('compressed corpus exceeds64KiB')
        sys.stderr.write(encode({'passed':plugin.passed,'vectors':len(vectors),'gzip_bytes':len(packed),'java_calls':java_calls})+'\\n')
        sys.stdout.buffer.write(packed)
        """;

    /** repo, exact python, verified machine_id, new scratch/output; optional Java/classpath for consumer substitution. */
    public static void main(String[] args) throws Exception {
        if (args.length != 5 && args.length != 7) { throw new IllegalArgumentException("repo python machine scratch output [java classpath] required"); }
        boolean differential = args.length == 7;
        Path repo = Path.of(args[0]).toAbsolutePath().normalize(), output = Path.of(args[4]).toAbsolutePath().normalize();
        Path scratch = Path.of(args[3]).toAbsolutePath().normalize();
        if (!Path.of(args[4]).isAbsolute() || !Path.of(args[3]).isAbsolute()
                || output.startsWith(repo) || scratch.startsWith(repo) || !output.startsWith(scratch)
                || Files.exists(output) || Files.exists(scratch) || args[2].isBlank()) {
            throw new IllegalArgumentException("new bounded external scratch/output and explicit machine identity required");
        }
        Files.createDirectory(scratch);
        List<String> command = new ArrayList<>(List.of(args[1], "-B", "-X", "utf8", "-c", SCRIPT, repo.toString(), args[2]));
        if (differential) { command.add(args[5]); command.add(args[6]); }
        ProcessBuilder builder = new ProcessBuilder(command); builder.directory(repo.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        for (String key : List.of("TMP", "TEMP", "TMPDIR")) { builder.environment().put(key, scratch.toString()); }
        Process process = builder.start();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout = executor.submit(() -> bounded(process.getInputStream(), 65536));
            var stderr = executor.submit(() -> bounded(process.getErrorStream(), 131072));
            try {
                if (!process.waitFor(120, TimeUnit.SECONDS)) { throw new IOException("original capture timeout120s"); }
                byte[] raw = stdout.get(10, TimeUnit.SECONDS); System.err.write(stderr.get(10, TimeUnit.SECONDS));
                if (process.exitValue() != 0 || raw.length == 0) { throw new IOException("original capture failed exit=" + process.exitValue()); }
                if (differential) { System.out.println("PASS original producer -> Java -> original consumers; golden not overwritten"); }
                else { Files.createDirectories(output.getParent()); Files.write(output, raw, StandardOpenOption.CREATE_NEW); System.out.println("WROTE " + output + " bytes=" + raw.length); }
            } finally { if (process.isAlive()) { process.destroyForcibly(); } }
        }
    }
    private static byte[] bounded(InputStream input, int maximum) throws IOException {
        try (input; ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192]; int count;
            while ((count = input.read(buffer)) != -1) { if (output.size() + count > maximum) { throw new IOException("capture output exceeded bound"); } output.write(buffer, 0, count); }
            return output.toByteArray();
        }
    }
}
