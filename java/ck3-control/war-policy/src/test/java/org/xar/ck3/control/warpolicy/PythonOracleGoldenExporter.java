package org.xar.ck3.control.warpolicy;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

/**
 * Test-only, one-shot capture of the unchanged Python regression oracle.
 * Run by the designated build writer before Maven, using Java 21 source mode.
 * It neither implements policy nor calls a native connection or game process.
 */
public final class PythonOracleGoldenExporter {
    private static final int CORPUS_MAX_BYTES = 2 * 1024 * 1024;
    private static final int STDERR_MAX_BYTES = 128 * 1024;
    private static final String OUTPUT = "java/ck3-control/war-policy/src/test/resources/"
        + "org/xar/ck3/control/warpolicy/war_outcome_stakes_golden_v1.jsonl";
    private static final String SCRIPT = """
        from copy import deepcopy
        from datetime import datetime, timezone
        import hashlib
        import json
        from pathlib import Path
        import sys
        import unittest

        repo = Path(sys.argv[1]).resolve()
        machine = sys.argv[2]
        if not machine or len(machine) > 256:
            raise SystemExit('explicit observed machine_id required')
        sdk = repo / 'ck3_autonomous_player/src'
        tools = repo / 'tools/g2_saved_campaign'
        sys.path[:0] = [str(sdk), str(tools), str(repo / 'ck3_autonomous_player/tests/unit')]
        import test_war_outcome_stakes_v1 as suite

        paths = (
            'tools/g2_saved_campaign/war_outcome_stakes_v1.py',
            'tools/g2_saved_campaign/test_war_outcome_stakes_v1.py',
            'tools/g2_saved_campaign/fixtures/war_outcome_stakes_source_v1.json',
            'ck3_autonomous_player/src/xar_autoplayer/bridge/war_contract.py',
            'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py',
            'ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py',
        )
        def pins():
            return {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in paths}
        before = pins()
        required = {
            paths[0]: 'e59b71b5479e98c0c225b36c45c91fda49403b3e1f897f59904d415b32256457',
            paths[1]: '0d55a99940be581981695906b693a74a84f4b9265971ae09494f3bb2c5f2fb76',
            paths[2]: 'd4e4369d587fc9257100f8c366aa1f284a7d0e9f7333992843184fc76ef60930',
        }
        if any(before[path] != expected for path, expected in required.items()):
            raise SystemExit('frozen oracle/test/registry pin differs; do not bless new golden')
        vectors = []
        current_test = None
        original = suite.stakes.project_war_outcome_stakes_v1
        def capture(snapshot, *, war_id, campaign_root, current_source_sha256, registry, observation_context):
            request = deepcopy({
                'schema': 'g2.war-outcome-stakes-request/v1', 'war_id': war_id,
                'snapshot': snapshot, 'campaign_root': campaign_root,
                'current_source_sha256': current_source_sha256,
                'observation_context': observation_context,
            })
            vector = {'test_method': current_test, 'ordinal': len(vectors) + 1,
                'input_json': json.dumps(request, allow_nan=False, ensure_ascii=False,
                    sort_keys=True, separators=(',', ':'))}
            try:
                result = original(snapshot, war_id=war_id, campaign_root=campaign_root,
                    current_source_sha256=current_source_sha256, registry=registry,
                    observation_context=observation_context)
            except ValueError:
                vector['expected_kind'] = 'invalid_contract'
                vectors.append(vector)
                raise
            vector['expected_kind'] = 'result'
            vector['expected'] = deepcopy(result)
            vectors.append(vector)
            return result
        class CaptureResult(unittest.TextTestResult):
            def startTest(self, test):
                global current_test
                current_test = test.id().rsplit('.', 1)[-1]
                super().startTest(test)
        names = unittest.defaultTestLoader.getTestCaseNames(suite.WarOutcomeStakesTests)
        if len(names) != 11:
            raise SystemExit('expected all original 11 methods')
        suite.stakes.project_war_outcome_stakes_v1 = capture
        try:
            result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2,
                resultclass=CaptureResult).run(
                    unittest.defaultTestLoader.loadTestsFromTestCase(suite.WarOutcomeStakesTests))
        finally:
            suite.stakes.project_war_outcome_stakes_v1 = original
        if not result.wasSuccessful() or result.testsRun != 11 or result.skipped:
            raise SystemExit('original regression not fully passed; golden refused')
        if pins() != before:
            raise SystemExit('source changed while generating golden')
        if set(v['test_method'] for v in vectors) != set(names):
            raise SystemExit('one of 11 methods produced no captured vector')
        header = {
            'schema': 'g2.war-outcome-stakes-golden/v1',
            'machine_id': machine,
            'observed_at_utc': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'source': 'unchanged-original-unittest-normalizer-native-cache-python-oracle',
            'source_sha256': before,
            'registry_sha256': suite.stakes.REGISTRY_SHA256,
            'test_methods': names, 'tests_run': result.testsRun, 'skips': 0,
            'vector_count': len(vectors),
            'native_game_rpc_count': 0,
            'service_decision_consumer_status': 'SOURCE_ONLY',
        }
        for row in [header, *vectors]:
            raw = json.dumps(row, allow_nan=False, ensure_ascii=False,
                sort_keys=True, separators=(',', ':')).encode('utf-8')
            if len(raw) > 65536:
                raise SystemExit('one golden row exceeds shared parser budget')
            sys.stdout.buffer.write(raw + b'\\n')
        """;

    private PythonOracleGoldenExporter() { }

    /** Arguments: absolute repo, exact Python executable, verified machine_id. */
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) { throw new IllegalArgumentException("repo python machine_id required"); }
        Path repo = Path.of(arguments[0]).toAbsolutePath().normalize();
        Path output = repo.resolve(OUTPUT).normalize();
        if (!output.startsWith(repo) || Files.exists(output)) {
            throw new IllegalArgumentException("new bounded repo golden path required; no overwrite");
        }
        ProcessBuilder builder = new ProcessBuilder(arguments[1], "-B", "-X", "utf8", "-c", SCRIPT,
            repo.toString(), arguments[2]);
        builder.directory(repo.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("PYTHONPATH", repo.resolve("ck3_autonomous_player/src")
            + java.io.File.pathSeparator + repo.resolve("tools/g2_saved_campaign")
            + java.io.File.pathSeparator + repo.resolve("ck3_autonomous_player/tests/unit"));
        Process process = builder.start();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            Future<byte[]> stdout = executor.submit(() -> boundedRead(process.getInputStream(), CORPUS_MAX_BYTES));
            Future<byte[]> stderr = executor.submit(() -> boundedRead(process.getErrorStream(), STDERR_MAX_BYTES));
            try {
                if (!process.waitFor(120, TimeUnit.SECONDS)) { throw new IOException("oracle timed out at 120s"); }
                byte[] raw = stdout.get(10, TimeUnit.SECONDS);
                byte[] errors = stderr.get(10, TimeUnit.SECONDS);
                System.err.write(errors);
                if (process.exitValue() != 0 || raw.length == 0 || raw[raw.length - 1] != '\n') {
                    throw new IOException("oracle failed, exit=" + process.exitValue());
                }
                Files.createDirectories(output.getParent());
                Files.write(output, raw, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
                System.out.println("WROTE " + output + " bytes=" + raw.length);
            } finally {
                if (process.isAlive()) { process.destroyForcibly(); }
            }
        }
    }

    private static byte[] boundedRead(InputStream stream, int maximum) throws IOException {
        try (stream; ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192];
            int count;
            while ((count = stream.read(buffer)) != -1) {
                if (output.size() + count > maximum) { throw new IOException("oracle output budget exceeded"); }
                output.write(buffer, 0, count);
            }
            return output.toByteArray();
        }
    }
}
