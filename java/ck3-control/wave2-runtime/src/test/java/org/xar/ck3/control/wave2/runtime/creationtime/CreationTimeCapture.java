package org.xar.ck3.control.wave2.runtime.creationtime;

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

/** Explicit local old-producer capture. Normal JUnit has no dependency on Python or a running process. */
public final class CreationTimeCapture {
    private static final String OUTPUT = "java/ck3-control/wave2-runtime/src/test/resources/creationtime/original-v1.jsonl.gz";
    private static final String SCRIPT = """
        from contextlib import redirect_stdout
        from datetime import datetime, timezone
        import gzip
        import hashlib
        import importlib
        import inspect
        import json
        from pathlib import Path
        import subprocess
        import sys
        import pytest
        repo, machine, scratch = Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3]).resolve()
        sys.path[:0] = [str(repo / 'ck3_autonomous_player/src'), str(repo / 'ck3_autonomous_player/tests/unit')]
        from xar_autoplayer import environment as leaf
        paths = ['ck3_autonomous_player/src/xar_autoplayer/' + path for path in (
            'environment.py', 'bridge/faction_gift_formal_route_v1.py',
            'bridge/construction_process_identity_v1.py', 'bridge/native_loaded_provider_custody_v1.py')]
        paths += ['ck3_autonomous_player/tests/unit/' + path for path in (
            'test_environment.py', 'test_faction_gift_formal_route_v1.py', 'test_construction_process_identity_kernel.py')]
        def pins():
            return {path: hashlib.sha256((repo / path).read_bytes()).hexdigest() for path in paths}
        before = pins()
        names = ('process_creation_utc', 'same_process_creation_time')
        original = {name: getattr(leaf, name) for name in names}
        vectors, seen, calls = [], set(), dict.fromkeys(names, 0)
        current, passed, skipped, total, diff_calls = 'manual-boundary', 0, 0, 0, 0
        probe = None
        if len(sys.argv) == 6:
            probe = subprocess.Popen([sys.argv[4], '-Xms16m', '-Xmx64m', '-XX:MaxMetaspaceSize=64m',
                '-cp', sys.argv[5], 'org.xar.ck3.control.wave2.runtime.creationtime.CreationTimeProbe'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr)
        def encode(value):
            return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
        def java_result(request):
            global diff_calls
            probe.stdin.write(request.encode('utf-8') + b'\\n')
            probe.stdin.flush()
            value = json.loads(probe.stdout.readline(4098))
            diff_calls += 1
            return value
        def wrap(name, fn):
            signature = inspect.signature(fn)
            def invoke(*args, **kwargs):
                calls[name] += 1
                request = encode({'schema': 'g2.wave2-runtime.creationtime-request/v1',
                    'operation': name, 'arguments': dict(signature.bind(*args, **kwargs).arguments)})
                try:
                    value = fn(*args, **kwargs)
                except (ValueError, TypeError, OverflowError):
                    key = (request, 'invalid_contract')
                    if key not in seen:
                        seen.add(key)
                        vectors.append({'ordinal': len(vectors) + 1, 'test_case': current,
                            'input': request, 'expected_kind': 'invalid_contract', 'expected': None})
                    if probe is not None and java_result(request) != {'test_transport_status': 'invalid_contract'}:
                        raise AssertionError('Java accepted unrepresentable birth timestamp')
                    raise
                wire = {'utc': value.isoformat()} if name == 'process_creation_utc' else {'same': value}
                key = (request, encode(wire))
                if key not in seen:
                    seen.add(key)
                    vectors.append({'ordinal': len(vectors) + 1, 'test_case': current,
                        'input': request, 'expected_kind': 'result', 'expected': wire})
                if probe is not None:
                    actual = java_result(request)
                    if encode(actual) != encode(wire):
                        raise AssertionError('Java birth mismatch ' + request + ' expected=' + encode(wire) + ' actual=' + encode(actual))
                    return datetime.fromisoformat(actual['utc']) if name == 'process_creation_utc' else actual['same']
                return value
            return invoke
        replacements = {name: wrap(name, fn) for name, fn in original.items()}
        for module in list(sys.modules.values()):
            namespace = getattr(module, '__dict__', {})
            for name, fn in original.items():
                if namespace.get(name) is fn:
                    namespace[name] = replacements[name]
        cases = [None, True, 12, '', 'None', 'null', 'historic-process-marker',
            '20260822090033.870978+480', '2026-08-22T01:00:33.8709780Z',
            '20260822090033.870978-480', '20260822090033.870978+840',
            '20260822090033.870978-840', '20260822090033.870978+841',
            '20260822090033.870978+999', '20260822090033.000000+000',
            '2026-08-22T09:00:33.0000000Z', '2026-08-22T01:00:33.8709781Z',
            '2026-08-22T01:00:33.8709789Z', '2026-08-22T01:00:33Z',
            '2026-08-22T01:00:33.870978Z', '2026-08-22T01:00:33.8709780+00:00',
            '20260822090033.******+480', '20240229000000.123456+000',
            '20230229000000.123456+000', '20261301000000.000000+000',
            '20260101240000.000000+000', '20260101000060.000000+000',
            '00010101000000.000000+000', '00010101000000.000000+001',
            '99991231235959.999999-000', '99991231235959.999999-001',
            '0001-01-01T00:00:00.0000000Z', '9999-12-31T23:59:59.9999990Z',
            '0000-01-01T00:00:00.0000000Z', '2026-08-22t01:00:33.8709780Z',
            '2026-08-22T01:00:33.8709780z']
        cases += [edge + '20260822090033.870978+480' + edge for edge in (
            ' ', '\\t\\r\\n', '\\x1c', '\\x85', '\\xa0', '\\u1680', '\\u2007', '\\u202f', '\\u3000', '\\u200b')]
        for value in cases:
            try:
                leaf.process_creation_utc(value)
            except (ValueError, TypeError, OverflowError):
                pass
            leaf.same_process_creation_time(value, cases[7])
            leaf.same_process_creation_time(value, value)
        class Trace:
            def pytest_runtest_setup(self, item):
                global current
                current = item.nodeid
            def pytest_runtest_logreport(self, report):
                global total, passed, skipped
                if report.when == 'call':
                    total += 1
                    passed += int(report.passed)
                if report.skipped:
                    skipped += 1
        selected = ['ck3_autonomous_player/tests/unit/test_environment.py::ProcessCreationTimeTests',
            'ck3_autonomous_player/tests/unit/test_construction_process_identity_kernel.py',
            'ck3_autonomous_player/tests/unit/test_faction_gift_formal_route_v1.py']
        with redirect_stdout(sys.stderr):
            code = pytest.main(['-q', '-p', 'no:cacheprovider', '--basetemp', str(scratch / 'pytest'), *selected], plugins=[Trace()])
        if code != 0 or skipped or total <= 0 or total != passed:
            raise SystemExit('original source/consumer extraction failed or skipped')
        if probe is not None:
            probe.stdin.close()
            if probe.wait(timeout=10) != 0:
                raise SystemExit('Java creation time pipe did not exit successfully')
        if pins() != before:
            raise SystemExit('original source changed during capture')
        header = {'schema': 'g2.wave2-runtime.creationtime-golden/v1', 'machine_id': machine,
            'observed_at_utc': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'source_sha256': before, 'original_tests': total, 'skips': skipped,
            'scope': selected, 'original_call_counts': calls, 'vector_count': len(vectors),
            'java_consumer_calls': diff_calls, 'native_game_rpc_count': 0, 'live_adoption': False}
        raw = b'\\n'.join([encode(header).encode('utf-8')] + [encode(vector).encode('utf-8') for vector in vectors]) + b'\\n'
        packed = gzip.compress(raw, mtime=0)
        if len(raw) > 2 * 1024 * 1024 or len(packed) > 32768:
            raise SystemExit('creation time capture exceeds finite budget')
        sys.stderr.write(encode({'original_tests': total, 'skips': skipped, 'vectors': len(vectors),
            'java_consumer_calls': diff_calls, 'gzip_bytes': len(packed)}) + '\\n')
        sys.stdout.buffer.write(packed)
        """;
    private CreationTimeCapture() { }
    /** Four capture args; fifth may be a new output inside scratch; six args run the original Java differential. */
    public static void main(String[] args) throws Exception {
        if (args.length != 4 && args.length != 5 && args.length != 6) { throw new IllegalArgumentException("repo python machine new-scratch [new-scratch-output | java classpath] required"); }
        boolean differential = args.length == 6; Path repo = Path.of(args[0]).toAbsolutePath().normalize();
        Path scratch = Path.of(args[3]).toAbsolutePath().normalize();
        Path output = args.length == 5 ? Path.of(args[4]).toAbsolutePath().normalize() : repo.resolve(OUTPUT);
        boolean outputPermitted = args.length == 5 ? scratch.equals(output.getParent()) : output.startsWith(repo);
        if (!outputPermitted || Files.exists(scratch) || !differential && Files.exists(output) || args[2].isBlank()) { throw new IllegalArgumentException("new bounded scratch/output and machine required"); }
        Files.createDirectory(scratch);
        List<String> command = new ArrayList<>(List.of(args[1], "-B", "-X", "utf8", "-c", SCRIPT, repo.toString(), args[2], scratch.toString()));
        if (differential) { command.add(args[4]); command.add(args[5]); }
        ProcessBuilder builder = new ProcessBuilder(command).directory(repo.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        for (String key : List.of("TMP", "TEMP", "TMPDIR")) { builder.environment().put(key, scratch.toString()); }
        Process process = builder.start();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout = executor.submit(() -> bounded(process.getInputStream(), 32768));
            var stderr = executor.submit(() -> bounded(process.getErrorStream(), 128 * 1024));
            try {
                if (!process.waitFor(120, TimeUnit.SECONDS)) { throw new IOException("creation time capture timed out at120s"); }
                byte[] raw = stdout.get(10, TimeUnit.SECONDS); System.err.write(stderr.get(10, TimeUnit.SECONDS));
                if (process.exitValue() != 0 || raw.length == 0) { throw new IOException("creation time capture failed exit=" + process.exitValue()); }
                if (differential) { System.out.println("PASS original producer to Java to actual original consumers; no golden overwrite"); }
                else { Files.createDirectories(output.getParent()); Files.write(output, raw, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE); System.out.println("WROTE " + output + " bytes=" + raw.length); }
            } finally { if (process.isAlive()) { process.destroyForcibly(); } }
        }
    }
    private static byte[] bounded(InputStream input, int maximum) throws IOException {
        try (input; ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[4096]; int count;
            while ((count = input.read(buffer)) != -1) { if (out.size() + count > maximum) { throw new IOException("creation time output cap"); } out.write(buffer, 0, count); }
            return out.toByteArray();
        }
    }
}
