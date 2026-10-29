package org.xar.ck3.control.score;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionDispatcher;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.ProjectionWire;
import org.xar.ck3.control.score.projection.CampaignArithmeticProjectionCatalog;

/** Seven named original reference consumers continue with Java results; no whole/current SDK or HTTP claim. */
final class CampaignArithmeticOriginalConsumerTest {
    private static final String SCRIPT = """
        from decimal import Decimal, DivisionByZero, InvalidOperation, Overflow, getcontext
        import hashlib, json, sys, unittest
        from pathlib import Path
        repo = Path(sys.argv[1]).resolve()
        protocol_out = sys.stdout
        paths = {
            'ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py':
                'ba4421fdc66048852e3c7a158a461e8fa2dad5d96c75904e4077e8797652dd4d',
            'ck3_autonomous_player/tests/unit/test_campaign_development_score_v1.py':
                '0525b7c2e6bd163706b2734b302f3bcad0fd588c50be59e9cbefec458d8c03c2',
            'ck3_autonomous_player/tools/score_ck3_campaign.py':
                'ba6493478872ee6c100360b689d1eed4c8aca6aee40463b44a7bf1b3f849b212',
        }
        def pins():
            return {name: hashlib.sha256((repo / name).read_bytes()).hexdigest() for name in paths}
        context = getcontext()
        if (pins() != paths or
                (context.prec, context.rounding, context.Emin, context.Emax, context.capitals, context.clamp)
                != (28, 'ROUND_HALF_EVEN', -999999, 999999, 1, 0) or
                any(context.traps[signal] != (signal in (InvalidOperation, DivisionByZero, Overflow))
                    for signal in context.traps)):
            raise SystemExit('actual unchanged original producer/consumers and decimal profile required')
        sys.path[:0] = [str(repo / 'ck3_autonomous_player/src'), str(repo / 'ck3_autonomous_player/tests/unit')]
        from xar_autoplayer import campaign_development_score_v1 as original
        import test_campaign_development_score_v1 as suite
        calls = {'aggregate': 0, 'score360': 0, 'display': 0}
        aggregate, history, display = original.aggregate_state, original.score_360, original.interval_text
        def transfer(operation, packet, expected):
            request = {'schema': 'g2.campaign-score-arithmetic/v1',
                'profile': 'python-decimal-default-28-half-even/v1', 'operation': operation, 'input': packet}
            print(json.dumps({'call': request}, ensure_ascii=True, allow_nan=False, separators=(',', ':')),
                  file=protocol_out, flush=True)
            response = sys.stdin.buffer.readline(65538)
            if not response or len(response) > 65537:
                raise AssertionError('missing/bounded Java arithmetic response')
            actual = json.loads(response)
            wanted = expected if isinstance(expected, str) else expected.export()
            if actual != wanted:
                raise AssertionError('actual Java arithmetic differs from true original: ' + operation)
            calls[operation] += 1
            return actual if isinstance(actual, str) else original.Interval(Decimal(actual['lower']), Decimal(actual['upper']))
        def aggregate_java(scores):
            return transfer('aggregate', {key: value.export() for key, value in scores.items()}, aggregate(scores))
        def history_java(samples, endpoint):
            expected = history(samples, endpoint)
            return transfer('score360', {'samples': [value.export() for value in samples], 'endpoint': endpoint.export()}, expected)
        def display_java(lower, upper, places=2):
            expected = display(lower, upper, places)
            return transfer('display', {'lower': str(original.dec(lower)), 'upper': str(original.dec(upper)), 'places': places}, expected)
        for module in (original, suite):
            module.aggregate_state, module.score_360, module.interval_text = aggregate_java, history_java, display_java
        selected = [
            'test_missing_baseline_is_interval_and_no_weight_redistribution',
            'test_debt_rescue_and_lost_half_reproduce_design',
            'test_gameover_denominator_and_incomplete_interval',
            'test_exported_repeating_decimals_have_exact_weighted_sum',
            'test_interval_display_outwards_and_partial_contribution_not_reweighted',
            'test_complete_explanations_negative_cash_and_strict_date',
            'test_cli_main_single_projection_scan_auto_map_and_export',
        ]
        result = unittest.TextTestRunner(stream=sys.stderr, verbosity=1).run(
            unittest.TestSuite(suite.CampaignScoreTests(name) for name in selected))
        if not result.wasSuccessful() or result.testsRun != len(selected) or result.skipped or pins() != paths:
            raise SystemExit('all seven named reference methods must finish unchanged without skips')
        if not all(calls.values()):
            raise SystemExit('every migrated arithmetic operation must reach its real consumer')
        print(json.dumps({'status': 'PASS', 'tests': result.testsRun, 'calls': calls,
                          'source_pre_post': 'MATCH', 'production_consumer_switched': False,
                          'reference_only': True, 'whole_original_suite': False, 'actual_http': False,
                          'game_rpc_calls': 0}, separators=(',', ':')), file=protocol_out, flush=True)
        """;

    @Test void actualJavaArithmeticContinuesOriginalReportHistoryAndCli() throws Exception {
        Path repo = requiredPath("XAR_ORACLE_REPO"), python = requiredPath("XAR_ORACLE_PYTHON");
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-B", "-X", "utf8", "-c", SCRIPT,
                repo.toString()).directory(repo.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Path temporary = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize();
        assertTrue(Files.isDirectory(temporary), "owned test temporary directory required");
        for (String key : new String[] {"TEMP", "TMP", "TMPDIR"}) { builder.environment().put(key, temporary.toString()); }
        Process process = builder.start();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var errors = executor.submit(() -> bounded(process.getErrorStream(), 32768));
            var interaction = executor.submit(() -> communicate(process));
            try {
                assertTrue(process.waitFor(90, TimeUnit.SECONDS), "original consumers timed out");
                byte[] error = errors.get(5, TimeUnit.SECONDS);
                assertEquals(0, process.exitValue(), new String(error, StandardCharsets.UTF_8));
                JsonNode result = interaction.get(5, TimeUnit.SECONDS);
                assertEquals("PASS", result.path("status").textValue());
                assertEquals(7, result.path("tests").intValue());
                for (String operation : new String[] {"aggregate", "score360", "display"}) {
                    assertTrue(result.path("calls").path(operation).intValue() > 0, operation);
                }
                assertEquals("MATCH", result.path("source_pre_post").textValue());
                assertFalse(result.path("production_consumer_switched").booleanValue());
                assertTrue(result.path("reference_only").booleanValue());
                assertFalse(result.path("whole_original_suite").booleanValue());
                assertFalse(result.path("actual_http").booleanValue());
                assertEquals(0, result.path("game_rpc_calls").intValue());
                System.out.println("ORIGINAL_SCORE_CONSUMERS " + result);
            } finally { if (process.isAlive()) { process.destroyForcibly(); } }
        }
    }

    private static JsonNode communicate(Process process) throws IOException {
        JsonNode result = null;
        ProjectionDispatcher dispatcher = ProjectionDispatcher.fromCatalogs(
                java.util.List.of(new CampaignArithmeticProjectionCatalog()));
        try (var reader = new BufferedReader(new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8));
                var input = process.getOutputStream()) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (line.length() > 65536) { throw new IOException("bounded original arithmetic request exceeded"); }
                JsonNode message = StrictJson.parse(line.getBytes(StandardCharsets.UTF_8));
                if (message.has("call")) {
                    ProjectionCall call = new ProjectionCall(new ProjectionCall.Identity("original-score-arithmetic",
                            ProjectionOperation.CAMPAIGN_ARITHMETIC_EVALUATE),
                            ProjectionJson.object(StrictJson.canonical(message.get("call")), 65536));
                    ProjectionResult.Succeeded succeeded = assertInstanceOf(ProjectionResult.Succeeded.class,
                            dispatcher.dispatch(ProjectionWire.encodeCall(call)));
                    byte[] response = succeeded.result().bytes();
                    input.write(response); input.write(10); input.flush();
                } else {
                    if (result != null) { throw new IOException("multiple original arithmetic terminal summaries"); }
                    result = message;
                }
            }
        } catch (IOException | RuntimeException failure) {
            process.destroyForcibly(); throw failure;
        }
        if (result == null) { throw new IOException("original arithmetic consumer terminal absent"); }
        return result;
    }
    private static Path requiredPath(String name) {
        String value = System.getenv(name);
        if (value == null || value.isBlank()) { throw new AssertionError(name + " required; missing environment is NOT_RUN"); }
        Path path = Path.of(value).toAbsolutePath().normalize(); assertTrue(Files.exists(path), name); return path;
    }
    private static byte[] bounded(java.io.InputStream stream, int limit) throws IOException {
        try (stream) {
            byte[] value = stream.readNBytes(limit + 1);
            if (value.length > limit) { throw new IOException("bounded original consumer stderr exceeded"); }
            return value;
        }
    }
}
