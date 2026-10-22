package org.xar.ck3.control.score;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Test-only oracle capture. Default JUnit consumes the committed JSONL without Python. */
public final class PythonScoreGoldenExporter {
    private static final int MAXIMUM_BYTES = 512 * 1024;
    private static final String OUTPUT = "java/ck3-control/campaign-score/src/test/resources/"
            + "org/xar/ck3/control/score/campaign_score_python_golden_v1.jsonl";
    private static final String SCRIPT = """
        from datetime import datetime, timezone
        from decimal import Decimal as D, InvalidOperation, getcontext
        import hashlib
        import json
        from pathlib import Path
        import sys
        import unittest
        repo = Path(sys.argv[1]).resolve()
        machine = sys.argv[2]
        if not machine or len(machine) > 256:
            raise SystemExit('explicit machine_id required')
        sys.path[:0] = [str(repo / 'ck3_autonomous_player/src'), str(repo / 'ck3_autonomous_player/tests/unit')]
        from xar_autoplayer import campaign_development_score_v1 as original
        import test_campaign_development_score_v1 as suite
        paths = {
            'ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py':
                'ba4421fdc66048852e3c7a158a461e8fa2dad5d96c75904e4077e8797652dd4d',
            'ck3_autonomous_player/tests/unit/test_campaign_development_score_v1.py':
                '0525b7c2e6bd163706b2734b302f3bcad0fd588c50be59e9cbefec458d8c03c2',
        }
        def pins():
            return {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in paths}
        if pins() != paths:
            raise SystemExit('original producer/test pin changed; do not bless new golden')
        vectors = []
        case = 'original-regression'
        aggregate = original.aggregate_state
        score = original.score_360
        display = original.interval_text
        def capture(operation, request, call):
            row = {'ordinal': len(vectors) + 1, 'case': case, 'operation': operation, 'input': request}
            try:
                value = call()
            except (ValueError, InvalidOperation):
                row['expected_kind'] = 'invalid_contract'
                vectors.append(row)
                raise
            row['expected_kind'] = 'result'
            row['expected'] = value if isinstance(value, str) else value.export()
            vectors.append(row)
            return value
        def aggregate_capture(scores):
            return capture('aggregate', {k: v.export() for k, v in scores.items()}, lambda: aggregate(scores))
        def score_capture(samples, endpoint):
            return capture('score360', {'samples': [v.export() for v in samples], 'endpoint': endpoint.export()},
                lambda: score(samples, endpoint))
        def display_capture(lower, upper, places=2):
            return capture('display', {'lower': str(original.dec(lower)), 'upper': str(original.dec(upper)), 'places': places},
                lambda: display(lower, upper, places))
        selected = [
            'test_missing_baseline_is_interval_and_no_weight_redistribution',
            'test_debt_rescue_and_lost_half_reproduce_design',
            'test_gameover_denominator_and_incomplete_interval',
            'test_exported_repeating_decimals_have_exact_weighted_sum',
            'test_interval_display_outwards_and_partial_contribution_not_reweighted',
        ]
        class Result(unittest.TextTestResult):
            def startTest(self, test):
                global case
                case = test.id().rsplit('.', 1)[-1]
                super().startTest(test)
        for module in (original, suite):
            module.aggregate_state = aggregate_capture
            module.score_360 = score_capture
            module.interval_text = display_capture
        try:
            result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2, resultclass=Result).run(
                unittest.TestSuite(suite.CampaignScoreTests(name) for name in selected))
        finally:
            for module in (original, suite):
                module.aggregate_state = aggregate
                module.score_360 = score
                module.interval_text = display
        if not result.wasSuccessful() or result.testsRun != 5 or result.skipped:
            raise SystemExit('original selected pure regression did not fully pass')
        I = original.Interval
        case = 'decimal40-sequential-sum-and-extreme-boundaries'
        sample = I(D('0.123456789012345678901234567890123456789012345'), D('99.999999999999999999999999999999999999999999'))
        score_capture([sample] * 360, sample)
        score_capture([I.exact('100')] * 360, I.exact('100'))
        score_capture([I.exact('0')] * 360, I.exact('-0'))
        for count in (0, 359, 361):
            try:
                score_capture([I.exact(70)] * count, I.exact(70))
            except ValueError:
                pass
        for samples, endpoint in (([I.exact('-0.0001')] * 360, I.exact(0)),
                ([I.exact(1)] * 360, I.exact(101))):
            try:
                score_capture(samples, endpoint)
            except ValueError:
                pass
        case = 'decimal80-fixed-domain-weights'
        long = I.exact('33.333333333333333333333333333333333333333333333333333333333333333333333333333333333333')
        aggregate_capture({name: long for name in original.DOMAINS})
        aggregate_capture({name: I(D('-0'), D('0')) for name in original.DOMAINS})
        case = 'display-outwards-ties-negative-zero-and-exponents'
        for lo, hi, places in [('1.005', '1.005', 2), ('1.015', '1.015', 2),
                ('-0.0001', '-0.0001', 2), ('-0.0001', '0.0001', 2), ('-1.005', '-1.005', 2),
                ('1E+2', '1E+2', 2), ('7.908', '25.561', 0), ('0', '1', 80)]:
            try:
                display_capture(lo, hi, places)
            except InvalidOperation:
                pass
        case = 'original-interval-export-lexical-roundtrip'
        for value in ('-0', '-0.00', '-0E+2', '1E+2', '1.2300', '0.0000001', '12345678901234567890'):
            interval = I.exact(value)
            capture('roundtrip', interval.export(), lambda interval=interval: interval)
        if pins() != paths:
            raise SystemExit('source changed during oracle capture')
        header = {'schema': 'g2.campaign-score-python-golden/v1', 'machine_id': machine,
            'observed_at_utc': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'source_sha256': paths, 'original_tests_run': result.testsRun, 'original_skips': 0,
            'original_test_methods': selected, 'vector_count': len(vectors),
            'decimal_default_precision': getcontext().prec, 'native_game_rpc_count': 0,
            'scope': ['Interval', 'aggregate_state', 'score_360', 'interval_text'],
            'not_migrated': ['state_intervals', 'quality_power', 'metric adapters', 'build_report', 'date qualification']}
        for row in [header, *vectors]:
            raw = json.dumps(row, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
            if len(raw) > 65536:
                raise SystemExit('golden line exceeds shared strict parser budget')
            sys.stdout.buffer.write(raw + bytes([10]))
        """;

    private PythonScoreGoldenExporter() { }

    /** Arguments: repo absolute path, existing Python executable, actual observed machine_id. */
    public static void main(String[] arguments) throws Exception {
        if (arguments.length != 3) { throw new IllegalArgumentException("repo python machine_id required"); }
        Path repo = Path.of(arguments[0]).toAbsolutePath().normalize();
        Path output = repo.resolve(OUTPUT).normalize();
        if (!output.startsWith(repo) || Files.exists(output)) { throw new IOException("new corpus path required; no overwrite"); }
        ProcessBuilder builder = new ProcessBuilder(arguments[1], "-B", "-X", "utf8", "-c", SCRIPT,
                repo.toString(), arguments[2]);
        builder.directory(repo.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Process process = builder.start();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout = executor.submit(() -> read(process.getInputStream(), MAXIMUM_BYTES));
            var stderr = executor.submit(() -> read(process.getErrorStream(), 32768));
            try {
                if (!process.waitFor(90, TimeUnit.SECONDS)) { throw new IOException("oracle timed out"); }
                byte[] raw = stdout.get(10, TimeUnit.SECONDS);
                byte[] error = stderr.get(10, TimeUnit.SECONDS);
                System.err.write(error);
                if (process.exitValue() != 0 || raw.length == 0 || raw[raw.length - 1] != 10) {
                    throw new IOException("oracle capture failed, exit=" + process.exitValue());
                }
                Files.createDirectories(output.getParent());
                Files.write(output, raw, StandardOpenOption.CREATE_NEW, StandardOpenOption.WRITE);
                System.out.println("WROTE " + output + " bytes=" + raw.length);
            } finally { if (process.isAlive()) { process.destroyForcibly(); } }
        }
    }

    private static byte[] read(InputStream stream, int maximum) throws IOException {
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
