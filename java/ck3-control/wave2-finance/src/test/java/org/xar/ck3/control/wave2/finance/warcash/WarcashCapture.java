package org.xar.ck3.control.wave2.finance.warcash;

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

/** Explicit bounded local capture/differential support, never a default Maven/CI Python dependency. */
public final class WarcashCapture {
    private static final String OUTPUT = "java/ck3-control/wave2-finance/src/test/resources/warcash/original-v1.jsonl.gz";
    private static final int MAX_GZIP = 65_536;
    private static final String SCRIPT = """
        from copy import deepcopy
        from datetime import datetime, timezone
        import gzip
        import hashlib
        import importlib
        import inspect
        import json
        from pathlib import Path
        import subprocess
        import sys
        import unittest
        repo = Path(sys.argv[1]).resolve()
        machine = sys.argv[2]
        sys.path[:0] = [str(repo / 'ck3_autonomous_player/src'), str(repo / 'ck3_autonomous_player/tests/unit')]
        from xar_autoplayer import m5_war_cash_resource_v1 as leaf
        names = ('observe_active_war_cash_resource_v1', 'require_complete_war_cash_resource_v1',
            'observe_aggregate_active_war_cash_resource_v1', 'require_complete_aggregate_war_cash_resource_v1')
        tests = ('test_m5_war_cash_resource_v1', 'test_m5_public_army_zero_claims',
            'test_m5_observed_opportunity_selector', 'test_m5_formal_proposal_collector')
        paths = ['ck3_autonomous_player/src/xar_autoplayer/' + name + '.py' for name in (
            'm5_war_cash_resource_v1', 'm5_observed_opportunity_selector', 'm5_formal_proposal_collector',
            'm5_joint_dispatch', 'm5_joint_budget_selector', 'bridge/service',
            'bridge/faction_gift_formal_route_v1', 'war_mercenary_consumer_v1',
            'bridge/readonly_planning_retry_v1', 'native_auto_run',
            'ordinary_player_risk_context_v1')]
        paths += ['ck3_autonomous_player/tests/unit/' + name + '.py' for name in tests]
        def pins():
            return {path: hashlib.sha256((repo / path).read_bytes()).hexdigest() for path in paths}
        before = pins()
        original = {name: getattr(leaf, name) for name in names}
        vectors, seen = [], set()
        calls = {name: 0 for name in names}
        current, differential = None, 0
        probe = None
        if len(sys.argv) == 5:
            probe = subprocess.Popen([sys.argv[3], '-Xms16m', '-Xmx96m', '-XX:MaxMetaspaceSize=64m',
                '-cp', sys.argv[4], 'org.xar.ck3.control.wave2.finance.warcash.WarcashProbe'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr)
        def encode(value):
            return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
        def java_result(raw):
            global differential
            probe.stdin.write(raw.encode('utf-8') + b'\\n')
            probe.stdin.flush()
            value = json.loads(probe.stdout.readline(65538))
            differential += 1
            return value
        def wrap(name, fn):
            signature = inspect.signature(fn)
            def invoke(*args, **kwargs):
                calls[name] += 1
                arguments = deepcopy(dict(signature.bind(*args, **kwargs).arguments))
                request = encode({'schema': 'g2.wave2-finance.warcash-request/v1',
                    'operation': name, 'arguments': arguments})
                try:
                    value = fn(*args, **kwargs)
                except (ValueError, TypeError):
                    key = (request, 'invalid_contract')
                    if key not in seen:
                        seen.add(key)
                        vectors.append({'ordinal': len(vectors) + 1, 'test_case': current,
                            'input': request, 'expected_kind': 'invalid_contract', 'expected': None})
                    if probe is not None and java_result(request) != {'test_transport_status': 'invalid_contract'}:
                        raise AssertionError('Java accepted invalid original cash contract')
                    raise
                key = (request, encode(value))
                if key not in seen:
                    seen.add(key)
                    vectors.append({'ordinal': len(vectors) + 1, 'test_case': current,
                        'input': request, 'expected_kind': 'result', 'expected': deepcopy(value)})
                if probe is not None:
                    actual = java_result(request)
                    if encode(actual) != encode(value):
                        raise AssertionError('Java cash mismatch ' + name + ' expected=' + encode(value)[:500] + ' actual=' + encode(actual)[:500])
                    return actual
                return value
            return invoke
        replacements = {name: wrap(name, fn) for name, fn in original.items()}
        for module in list(sys.modules.values()):
            namespace = getattr(module, '__dict__', {})
            for name, fn in original.items():
                if namespace.get(name) is fn:
                    namespace[name] = replacements[name]
        class Result(unittest.TextTestResult):
            def startTest(self, test):
                global current
                current = test.id()
                super().startTest(test)
        collection = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module(name)) for name in tests)
        result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2, resultclass=Result).run(collection)
        if not result.wasSuccessful() or result.skipped or not result.testsRun or any(not count for count in calls.values()):
            raise SystemExit('full original producer/consumer suite failed, skipped, or missed an operation')
        if probe is not None:
            probe.stdin.close()
            if probe.wait(timeout=10) != 0:
                raise SystemExit('Java consumer pipe did not close successfully')
        if pins() != before:
            raise SystemExit('source changed during sampling')
        header = {'schema': 'g2.wave2-finance.warcash-golden/v1', 'machine_id': machine,
            'observed_at_utc': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'source_sha256': before, 'original_tests': result.testsRun, 'skips': 0,
            'original_call_counts': calls, 'vector_count': len(vectors), 'java_consumer_calls': differential,
            'test_modules': list(tests), 'native_game_rpc_count': 0, 'live_adoption': False,
            'format': 'header then metadata/raw-request/expected triples; original token spelling retained'}
        lines = [encode(header).encode('utf-8')]
        for vector in vectors:
            request, expected = vector['input'].encode('utf-8'), encode(vector['expected']).encode('utf-8')
            if len(request) > 65536 or len(expected) > 65536:
                raise SystemExit('actual vector exceeds declared wire budget; no silent omission')
            lines.extend([encode({key: vector[key] for key in ('ordinal', 'test_case', 'expected_kind')}).encode('utf-8'), request, expected])
        raw = b'\\n'.join(lines) + b'\\n'
        if len(raw) > 8 * 1024 * 1024:
            raise SystemExit('raw sampling exceeds 8MiB')
        packed = gzip.compress(raw, mtime=0)
        if len(packed) > 65536:
            raise SystemExit('actual compressed corpus exceeds 64KiB allocation')
        sys.stderr.write(encode({'original_tests': result.testsRun, 'skips': 0,
            'vectors': len(vectors), 'java_consumer_calls': differential, 'gzip_bytes': len(packed)}) + '\\n')
        sys.stdout.buffer.write(packed)
        """;
    private WarcashCapture() { }
    /** Four capture args; fifth may be a new output inside scratch; six args run the original Java differential. */
    public static void main(String[] args) throws Exception {
        if (args.length != 4 && args.length != 5 && args.length != 6) { throw new IllegalArgumentException("repo python machine scratch [new-scratch-output | java classpath] required"); }
        boolean differential = args.length == 6;
        Path repo = Path.of(args[0]).toAbsolutePath().normalize(), scratch = Path.of(args[3]).toAbsolutePath().normalize();
        Path output = args.length == 5 ? Path.of(args[4]).toAbsolutePath().normalize() : repo.resolve(OUTPUT).normalize();
        boolean outputPermitted = args.length == 5 ? scratch.equals(output.getParent()) : output.startsWith(repo);
        if (!outputPermitted || !differential && Files.exists(output) || Files.exists(scratch) || args[2].isBlank()) {
            throw new IllegalArgumentException("new bounded output/scratch and explicit machine_id required");
        }
        Files.createDirectory(scratch);
        List<String> command = new ArrayList<>(List.of(args[1], "-B", "-X", "utf8", "-c", SCRIPT, repo.toString(), args[2]));
        if (differential) { command.add(args[4]); command.add(args[5]); }
        ProcessBuilder builder = new ProcessBuilder(command); builder.directory(repo.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        for (String key : List.of("TMP", "TEMP", "TMPDIR")) { builder.environment().put(key, scratch.toString()); }
        Process process = builder.start();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout = executor.submit(() -> bounded(process.getInputStream(), MAX_GZIP));
            var stderr = executor.submit(() -> bounded(process.getErrorStream(), 128 * 1024));
            try {
                if (!process.waitFor(120, TimeUnit.SECONDS)) { throw new IOException("war cash capture timeout at120s"); }
                byte[] raw = stdout.get(10, TimeUnit.SECONDS); System.err.write(stderr.get(10, TimeUnit.SECONDS));
                if (process.exitValue() != 0 || raw.length == 0) { throw new IOException("war cash capture failed exit=" + process.exitValue()); }
                if (differential) { System.out.println("PASS original producer-to-Java-to-consumers; no golden overwrite"); }
                else { Files.createDirectories(output.getParent()); Files.write(output, raw, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE); System.out.println("WROTE " + output + " bytes=" + raw.length); }
            } finally { if (process.isAlive()) { process.destroyForcibly(); } }
        }
    }
    private static byte[] bounded(InputStream input, int maximum) throws IOException {
        try (input; ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192]; int count;
            while ((count = input.read(buffer)) != -1) { if (out.size() + count > maximum) { throw new IOException("war cash capture output limit"); } out.write(buffer, 0, count); }
            return out.toByteArray();
        }
    }
}
