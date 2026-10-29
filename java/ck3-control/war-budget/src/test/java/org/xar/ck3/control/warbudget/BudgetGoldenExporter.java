package org.xar.ck3.control.warbudget;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Original-consumer capture and differential fixture. All subprocesses stay in the shared bounded Job. */
public final class BudgetGoldenExporter {
    private static final String OUTPUT = "java/ck3-control/war-budget/src/test/resources/org/xar/ck3/control/warbudget/budget_golden_v1.jsonl.gz";
    private static final int MAX_GZIP_BYTES = 360 * 1024;
    private static final String SCRIPT = """
        from copy import deepcopy
        from datetime import datetime, timezone
        import contextlib
        import gzip
        import hashlib
        import inspect
        import importlib
        import importlib.util
        import json
        import os
        import subprocess
        from pathlib import Path
        from types import SimpleNamespace
        import sys
        import pytest
        repo = Path(sys.argv[1]).resolve()
        machine, temporary = sys.argv[2], str(Path(sys.argv[3]) / 'pytest')
        probe = None
        if len(sys.argv) == 6:
            probe = subprocess.Popen([sys.argv[4], '-Xms16m', '-Xmx48m', '-XX:+UseSerialGC',
                '-XX:ActiveProcessorCount=2', '-XX:MaxMetaspaceSize=64m',
                '-XX:ReservedCodeCacheSize=16m', '-XX:MaxDirectMemorySize=8m', '-Xss256k',
                '-cp', sys.argv[5], 'org.xar.ck3.control.warbudget.BudgetProbeMain'],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr)
        sys.path[:0] = [str(repo / 'ck3_autonomous_player/src'), str(repo / 'ck3_autonomous_player/tests/unit')]
        from xar_autoplayer import war_emergency_budget_v1 as budget
        names = ('priority_emergency_level_v1', 'observe_emergency_policy_v1',
            'valid_saved_emergency_revision_v1', 'emergency_quote_budget_v1', 'observe_emergency_recovery_v1')
        originals = {name: getattr(budget, name) for name in names}
        paths = ['ck3_autonomous_player/src/xar_autoplayer/' + name + '.py' for name in (
            'war_emergency_budget_v1', 'war_reinforcement_finance_v1', 'war_political_survival_stakes_v1',
            'war_reinforcement_tradeoff_v1', 'war_strategic_reserve_v1', 'war_mercenary_consumer_v1',
            'construction_formal_consumer', 'm5_observed_opportunity_selector', 'activity_feast_stage5_budget_v1',
            'bridge/version_identity', 'bridge/domain_construction_private_transport_v1',
            'bridge/native_driver', 'bridge/service', 'bridge/mcp_server')]
        tests = ['ck3_autonomous_player/tests/unit/' + name + '.py' for name in (
            'test_war_emergency_budget_v1', 'test_war_crisis_spend_down_v1', 'test_war_political_survival_stakes_v1')]
        paths += tests + ['ck3_autonomous_player/tests/unit/test_war_reinforcement_tradeoff_v1.py']
        def pins():
            return {path: hashlib.sha256((repo / path).read_bytes()).hexdigest() for path in paths}
        before = pins()
        compatibility = None
        compatibility_paths = {}
        fixture_calls = {name: 0 for name in names}
        fixture_context_checks = 0
        if probe is not None:
            candidate_path = Path(os.environ['XAR_BUDGET_COMPAT_CANDIDATE']).resolve()
            reference = json.loads(os.environ['XAR_SCORE_REFERENCE_CLIENT_REF'])
            if type(reference) is not dict or set(reference) != {'path','bytes','sha256'} or type(reference['path']) is not str or type(reference['bytes']) is not int or not 1 <= reference['bytes'] <= 1048576 or type(reference['sha256']) is not str:
                raise SystemExit('explicit closed reference-only client FileRef required')
            client_path = Path(reference['path']).resolve(strict=True)
            compatibility_paths = {str(candidate_path): 'd3938c90c626d2ccc24a14125da217a8551e9c7367703aa5b159d0ec04a717fd',
                str(client_path): reference['sha256']}
            def compatibility_pins():
                if client_path.stat().st_size != reference['bytes']: raise SystemExit('reference-only client source size drift')
                return {path: hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in compatibility_paths}
            if compatibility_pins() != compatibility_paths:
                raise SystemExit('exact mechanical candidate and explicitly pinned reference-only client required')
            def load(name, path):
                spec = importlib.util.spec_from_file_location(name, path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[name] = module
                spec.loader.exec_module(module)
                return module
            sys.path.insert(0, str(repo))
            client = load('tools.g2_saved_campaign.java_map_admission_client_v1', client_path)
            importlib.import_module('tools.g2_saved_campaign').java_map_admission_client_v1 = client
            fixture_config = object()
            def exchange(*, operation, payload, request_id):
                assert operation is client.ProjectionOperation.WAR_BUDGET_EVALUATE
                packet = client.decode_projection_object_v1(payload, maximum_bytes=65536)
                assert packet['schema'] == 'g2.war-budget-request/v1' and packet['operation'] in fixture_calls
                fixture_calls[packet['operation']] += 1
                probe.stdin.write(payload + b'\\n')
                probe.stdin.flush()
                raw = probe.stdout.readline(16386)
                assert raw and len(raw) <= 16385
                value = json.loads(raw)
                if value == {'test_transport_status': 'invalid_contract'}:
                    raise ValueError('actual registered Java budget rejected original invalid contract')
                result_bytes = client.encode_projection_json_v1(value, maximum_bytes=16384)
                return SimpleNamespace(require_success=lambda: result_bytes, http_call=None,
                    response_bytes=result_bytes, operation=operation, request_id=request_id, payload_bytes=payload)
            def check(result, *, config, operation, request_id, payload):
                global fixture_context_checks
                assert config is fixture_config and result.operation is operation
                assert result.request_id == request_id and result.payload_bytes == payload
                fixture_context_checks += 1
            # Explicit test-only issuance fixture. Actual shared-client HTTP qualification remains separate.
            client.require_current_projection_config_v1 = lambda: fixture_config
            client.call_current_projection_v1 = exchange
            client.require_result_context_v1 = check
            compatibility = load('xar_autoplayer._mechanical_budget_fixture', candidate_path)
        vectors, seen = [], set()
        current, totals = None, {'passed': 0, 'failed': 0, 'skipped': 0}
        raw_calls = {name: 0 for name in names}
        differential_calls = 0
        def encode(value):
            return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':'))
        def wrapper(name, original):
            signature = inspect.signature(original)
            def call(*args, **kwargs):
                global differential_calls
                bound = signature.bind(*args, **kwargs)
                request = {'schema': 'g2.war-budget-request/v1', 'operation': name,
                    'arguments': deepcopy(dict(bound.arguments))}
                input_json = encode(request)
                raw_calls[name] += 1
                try:
                    output = original(*args, **kwargs)
                except (ValueError, TypeError):
                    result = {'expected_kind': 'invalid_contract'}
                    key = (input_json, 'invalid_contract')
                    if key not in seen:
                        seen.add(key)
                        vectors.append({'ordinal': len(vectors) + 1, 'test_case': current,
                            'input_json': input_json, **result})
                    if probe is not None:
                        try:
                            getattr(compatibility, name)(*args, **kwargs)
                        except (ValueError, TypeError):
                            pass
                        else:
                            raise AssertionError('mechanical candidate accepted original invalid contract')
                        differential_calls += 1
                    raise
                key = (input_json, encode(output))
                if key not in seen:
                    seen.add(key)
                    vectors.append({'ordinal': len(vectors) + 1, 'test_case': current,
                        'input_json': input_json, 'expected_kind': 'result', 'expected': deepcopy(output)})
                if probe is not None:
                    observed = getattr(compatibility, name)(*args, **kwargs)
                    if encode(observed) != encode(output):
                        raise AssertionError('Java differential mismatch: ' + name + ' expected=' + encode(output)[:600] + ' actual=' + encode(observed)[:600])
                    differential_calls += 1
                    return observed
                return output
            return call
        replacements = {name: wrapper(name, original) for name, original in originals.items()}
        # Existing importers are updated only in this disposable local test process.
        for module in list(sys.modules.values()):
            namespace = getattr(module, '__dict__', {})
            for name, original in originals.items():
                if namespace.get(name) is original:
                    namespace[name] = replacements[name]
        class Track:
            def pytest_runtest_setup(self, item):
                global current
                current = item.nodeid
            def pytest_runtest_logreport(self, report):
                if report.when == 'call' and report.passed:
                    totals['passed'] += 1
                if report.failed:
                    totals['failed'] += 1
                if report.skipped:
                    totals['skipped'] += 1
        with contextlib.redirect_stdout(sys.stderr):
            exit_code = pytest.main([str(repo / path) for path in tests] +
                ['-q', '-p', 'no:cacheprovider', '--basetemp', temporary], plugins=[Track()])
        if exit_code != 0 or totals['failed'] or totals['skipped'] or not totals['passed']:
            raise SystemExit('whole original modules failed/skipped; corpus refused')
        if probe is not None:
            probe.stdin.close()
            if probe.wait(timeout=10) != 0:
                raise SystemExit('Java test pipe did not terminate cleanly')
        if pins() != before or any(not count for count in raw_calls.values()):
            raise SystemExit('source drift or operation not exercised; corpus refused')
        if probe is not None and (compatibility_pins() != compatibility_paths or
                any(not count for count in fixture_calls.values()) or fixture_context_checks == 0):
            raise SystemExit('mechanical candidate/client drift or missing public wrapper coverage')
        header = {'schema': 'g2.war-budget-golden/v1', 'machine_id': machine,
            'observed_at_utc': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'source_sha256': before, 'original_tests': totals, 'original_call_counts': raw_calls,
            'vector_count': len(vectors), 'source': 'unchanged-original-producer-and-consumer-tests',
            'default_ci_mode': 'frozen_vectors_only', 'native_game_rpc_count': 0,
            'java_consumer_differential_calls': differential_calls,
            'mechanical_wrapper_calls': fixture_calls, 'fixture_context_checks': fixture_context_checks,
            'compatibility_source_sha256': compatibility_paths,
            'shared_client_issuance_fixture': probe is not None, 'actual_http': False,
            'format': 'header then metadata/request/expected triples; request text retained exactly'}
        lines = [encode(header).encode('utf-8')]
        for vector in vectors:
            request = vector['input_json'].encode('utf-8')
            expected = encode(vector.get('expected')).encode('utf-8')
            if len(request) > 65536 or len(expected) > 16384:
                raise SystemExit('one vector exceeds strict wire budget; do not silently omit')
            lines.extend([encode({key: vector[key] for key in ('ordinal', 'test_case', 'expected_kind')}).encode('utf-8'), request, expected])
        raw = b'\\n'.join(lines) + b'\\n'
        if len(raw) > 8 * 1024 * 1024:
            raise SystemExit('decompressed corpus exceeds 8MiB')
        packed = gzip.compress(raw, mtime=0)
        if len(packed) > 360 * 1024:
            raise SystemExit('compressed corpus exceeds module allocation')
        sys.stderr.write(encode({'original_tests': totals, 'java_consumer_differential_calls': differential_calls,
            'unique_vectors': len(vectors), 'gzip_bytes': len(packed),
            'mechanical_wrapper_calls': fixture_calls, 'fixture_context_checks': fixture_context_checks,
            'shared_client_issuance_fixture': probe is not None, 'actual_http': False,
            'reference_only': True, 'current_sdk_qualified': False}) + '\\n')
        sys.stdout.buffer.write(packed)
        """;

    private BudgetGoldenExporter() { }
    /** Four capture args; fifth may be a new output inside scratch; six args run the original Java differential. */
    public static void main(String[] args) throws Exception {
        if (args.length != 4 && args.length != 5 && args.length != 6) { throw new IllegalArgumentException("repo python machine_id new-scratch [new-scratch-output | java classpath] required"); }
        boolean differential = args.length == 6;
        Path repo = Path.of(args[0]).toAbsolutePath().normalize(), scratch = Path.of(args[3]).toAbsolutePath().normalize();
        Path output = args.length == 5 ? Path.of(args[4]).toAbsolutePath().normalize() : repo.resolve(OUTPUT).normalize();
        boolean outputPermitted = args.length == 5 ? scratch.equals(output.getParent()) : output.startsWith(repo);
        if (!outputPermitted || !differential && Files.exists(output) || Files.exists(scratch) || args[2].isBlank()) {
            throw new IllegalArgumentException("new output and new scratch required; no overwrite");
        }
        Files.createDirectory(scratch);
        var command = new java.util.ArrayList<>(java.util.List.of(args[1], "-B", "-X", "utf8", "-c", SCRIPT, repo.toString(), args[2], args[3]));
        if (differential) { command.add(args[4]); command.add(args[5]); }
        ProcessBuilder builder = new ProcessBuilder(command);
        builder.directory(repo.toFile()); builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        if (differential) {
            String value = System.getenv("XAR_SCORE_REFERENCE_CLIENT_REF");
            if (value == null || value.isBlank()) throw new IOException("Explicit reference-only client FileRef required");
            var reference = org.xar.ck3.control.contracts.ExactRef.fromJson(org.xar.ck3.control.contracts.StrictJson.parse(
                    value.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
            Path source = Path.of(reference.path());
            if (!source.isAbsolute() || reference.bytes() < 1 || reference.bytes() > 1_048_576 || Files.size(source) != reference.bytes())
                throw new IOException("Bounded absolute reference-only client source required");
            String sha = java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(source)));
            if (!sha.equals(reference.sha256())) throw new IOException("Reference-only client source digest differs");
            builder.environment().put("XAR_SCORE_REFERENCE_CLIENT_REF", new String(
                    org.xar.ck3.control.contracts.StrictJson.canonical(reference.toJson()), java.nio.charset.StandardCharsets.UTF_8));
        }
        builder.environment().put("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1");
        // The original MCP fixture imports NumPy/OpenBLAS; bound its native worker pool too.
        for (String key : java.util.List.of("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")) {
            builder.environment().put(key, "1");
        }
        for (String key : java.util.List.of("TMP", "TEMP", "TMPDIR")) { builder.environment().put(key, scratch.toString()); }
        Process process = builder.start();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout = executor.submit(() -> bounded(process.getInputStream(), MAX_GZIP_BYTES));
            var stderr = executor.submit(() -> bounded(process.getErrorStream(), 128 * 1024));
            try {
                if (!process.waitFor(120, TimeUnit.SECONDS)) { throw new IOException("original test capture timed out"); }
                byte[] raw = stdout.get(10, TimeUnit.SECONDS); System.err.write(stderr.get(10, TimeUnit.SECONDS));
                if (process.exitValue() != 0 || raw.length == 0) { throw new IOException("capture failed exit=" + process.exitValue()); }
                if (differential) { System.out.println("PASS reference-only original consumers used actual Java pipe; no golden overwrite"); }
                else {
                    Files.createDirectories(output.getParent()); Files.write(output, raw, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
                    System.out.println("WROTE " + output + " bytes=" + raw.length);
                }
            } finally { if (process.isAlive()) { process.destroyForcibly(); } }
        }
    }
    private static byte[] bounded(InputStream input, int limit) throws IOException {
        try (input; ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192]; int count;
            while ((count = input.read(buffer)) != -1) { if (output.size() + count > limit) { throw new IOException("capture output limit"); } output.write(buffer, 0, count); }
            return output.toByteArray();
        }
    }
}
