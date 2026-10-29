package org.xar.ck3.control.wave3.planning.scorestate;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Test-only unchanged-producer capture. Default Maven/JUnit needs no Python. */
public final class StateScoreGoldenExporter {
    private static final String SCRIPT = """
        from copy import deepcopy
        from datetime import datetime, timezone
        from decimal import Decimal, DecimalException, getcontext
        import hashlib
        import inspect
        import json
        from pathlib import Path
        import sys
        import unittest
        repo = Path(sys.argv[1]).resolve()
        machine = sys.argv[2]
        sys.path[:0] = [str(repo / 'ck3_autonomous_player/src'), str(repo / 'ck3_autonomous_player/tests/unit')]
        from xar_autoplayer import campaign_development_score_v1 as original
        import test_campaign_development_score_v1 as suite
        expected = {
            'ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py':
                'ba4421fdc66048852e3c7a158a461e8fa2dad5d96c75904e4077e8797652dd4d',
            'ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py':
                'ffd650323c016b03204517f8ff460f1907ff603057b773372e1c836a74e19b2e',
            'ck3_autonomous_player/src/xar_autoplayer/campaign_score_target_projection.py':
                '749742086fa8977c2eafa0593801fe4328228a485ebe5f9178006ee823bb0006',
            'ck3_autonomous_player/tests/unit/test_campaign_development_score_v1.py':
                '0525b7c2e6bd163706b2734b302f3bcad0fd588c50be59e9cbefec458d8c03c2',
            'ck3_autonomous_player/tools/score_ck3_campaign.py':
                'ba6493478872ee6c100360b689d1eed4c8aca6aee40463b44a7bf1b3f849b212',
        }
        def pins():
            return {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in expected}
        if pins() != expected:
            raise SystemExit('unchanged original state/CLI/test source required')
        vectors, unique = [], {}
        packets, packet_indices = [], {}
        def packet_index(packet):
            raw = json.dumps(packet, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(',', ':'), default=str)
            if raw not in packet_indices:
                packet_indices[raw] = len(packets)
                packets.append(raw)
            return packet_indices[raw]
        case = 'original-suite'
        state = original.state_intervals
        def capture(current, baseline):
            request = json.dumps({'current': current, 'baseline': baseline}, ensure_ascii=False,
                allow_nan=False, sort_keys=True, separators=(',', ':'), default=str)
            # Observe real call sites, including all three build_report state evaluations and CLI.main.
            caller = sorted({frame.function for frame in inspect.stack()[1:8]
                if frame.function in ('build_report', 'main')})
            row = {'ordinal': len(vectors) + 1, 'captured_in': [case], 'callers': caller,
                'current_packet': packet_index(current), 'baseline_packet': packet_index(baseline)}
            try:
                value = state(current, baseline)
            except (ValueError, TypeError, AttributeError, KeyError, DecimalException) as error:
                row['expected_kind'] = 'invalid_contract'
                row['original_exception'] = type(error).__name__
                vectors.append(row)
                raise
            row['expected_kind'] = 'result'
            row['expected'] = {name: interval.export() for name, interval in value.items()}
            row['aggregate'] = original.aggregate_state(value).export()
            key = request + json.dumps(row['expected'], sort_keys=True, separators=(',', ':'))
            if key in unique:
                existing = unique[key]
                existing['captured_in'] = sorted(set(existing['captured_in'] + [case]))
                existing['callers'] = sorted(set(existing['callers'] + caller))
            else:
                row['ordinal'] = len(vectors) + 1
                vectors.append(row)
                unique[key] = row
            return value
        selected = [
            'test_missing_baseline_is_interval_and_no_weight_redistribution',
            'test_debt_rescue_and_lost_half_reproduce_design',
            'test_exported_repeating_decimals_have_exact_weighted_sum',
            'test_interval_display_outwards_and_partial_contribution_not_reweighted',
            'test_complete_explanations_negative_cash_and_strict_date',
            'test_cli_main_single_projection_scan_auto_map_and_export',
        ]
        class Result(unittest.TextTestResult):
            def startTest(self, test):
                global case
                case = test.id().rsplit('.', 1)[-1]
                super().startTest(test)
        for module in (original, suite):
            module.state_intervals = capture
        try:
            result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2, resultclass=Result).run(
                unittest.TestSuite(suite.CampaignScoreTests(name) for name in selected))
        finally:
            for module in (original, suite):
                module.state_intervals = state
        if not result.wasSuccessful() or result.testsRun != len(selected) or result.skipped:
            raise SystemExit('all six original pure/report/CLI methods must pass without skips')
        def run(label, current, baseline=None):
            global case
            case = label
            try:
                capture(current, {} if baseline is None else baseline)
            except (ValueError, TypeError, AttributeError, KeyError, DecimalException):
                pass
        m = suite.metrics
        seed = m(Q_realm=10, K_dynasty=10, legacy_ranks=1, control_average='.875', rebel_share='.125',
            gold=100, gross_income=10, total_expenses=3, military_current=1, military_all_raised=4,
            due_commitments=0, P_quality=250, continuation_legal=1, backup_heirs=2)
        run('all-missing', {})
        run('all-observed-baseline-fallback-discretionary', seed, seed)
        changed = deepcopy(seed)
        for name in ('Q_realm', 'K_dynasty', 'control_average', 'rebel_share'):
            changed[name] = {'availability': 'bounded', 'unit': original.UNITS[name],
                'lower': '0.123456789012345678901234567890123456789012345678901234567890123456789012345678901234567',
                'upper': '0.987654321098765432109876543210987654321098765432109876543210987654321098765432109876543'}
        run('bounded-decimal40-and-interval80-steps', changed, changed)
        for name, value in [('Q_realm', True), ('Q_realm', 1.0), ('Q_realm', None),
                ('legacy_ranks', '.5'), ('backup_heirs', '.5'), ('continuation_legal', '.5'),
                ('control_average', '1.0001'), ('due_commitments', '-1'), ('house_anchor_id', True)]:
            changed = deepcopy(seed); changed[name] = {'availability': 'observed', 'unit': original.UNITS[name], 'value': value}
            run('observed-invalid-' + name + '-' + str(value), changed, seed)
        for name in ('Q_realm', 'gross_income'):
            changed = deepcopy(seed); changed[name] = None
            run('explicit-null-row-' + name, changed, seed)
        changed = deepcopy(seed); changed['Q_realm'] = []
        run('empty-array-is-not-missing-row', changed, seed)
        changed = deepcopy(seed); changed['Q_realm'] = {'availability': 'unknown', 'unit': False, 'value': 1.0}
        run('unknown-does-not-validate-unused-unit-or-decimal', changed, seed)
        changed = deepcopy(seed); changed['Q_realm']['availability'] = []
        run('unhashable-availability-rejected', changed, seed)
        changed = deepcopy(seed); changed['house_anchor_id'] = {'availability': 'observed', 'unit': 'wrong', 'value': '1'}
        run('even-unused-observed-registry-unit-is-validated', changed, seed)
        changed = deepcopy(seed); changed['Q_realm'] = {'availability': 'bounded', 'unit': original.UNITS['Q_realm'], 'lower': '2', 'upper': '1'}
        run('reversed-bounds', changed, seed)
        changed = deepcopy(seed); changed['control_average'] = {'availability': 'bounded', 'unit': 'fraction', 'lower': '0', 'upper': '1.01'}
        run('bounded-fraction-above-one', changed, seed)
        changed = deepcopy(seed); changed['Q_realm'] = {'availability': 'bounded', 'unit': original.UNITS['Q_realm'], 'lower': None}
        run('missing-and-null-bounds-not-zero', changed, seed)
        run('deficit-with-incomplete-baseline-stays-zero-to25', m(gold=0, gross_income=1, total_expenses=2))
        changed = deepcopy(seed); changed.update(m(gold=-100, total_expenses=13, due_commitments=10))
        run('negative-cash-debt-and-deficit-cap', changed, seed)
        changed = deepcopy(seed); changed.update(m(military_current=4))
        run('current-military-exceeds-expenses', changed, seed)
        changed = deepcopy(seed); changed.update(m(military_current=4))
        run('baseline-invalid-fallback-expenses', seed, changed)
        changed.update(m(u_discretionary=1))
        run('explicit-baseline-discretionary-does-not-enter-fallback', seed, changed)
        run('zero-power-with-unknown-baseline-is-exact-zero', m(P_quality=0))
        for legal in ('0', '1'):
            run('continuation-known-backup-unknown-' + legal, m(continuation_legal=legal))
        changed = deepcopy(seed)
        for name in ('Q_realm', 'K_dynasty', 'legacy_ranks', 'control_average', 'rebel_share', 'gold', 'due_commitments'):
            changed[name]['value'] = '-0.00'
        run('signed-zero-through-subtraction-and-shared-intervals', changed, changed)
        changed = deepcopy(seed)
        changed['Q_realm']['value'] = '1.234567890123456789012345678901234567890123456789'
        changed['P_quality']['value'] = '123.4567890123456789012345678901234567890123456789'
        changed['gross_income']['value'] = '7.1234567890123456789012345678901234567890123456789'
        run('decimal40-intermediate-rounding-not-final-only', changed, seed)
        changed = m(Q_realm=0, P_quality=0, continuation_legal=0, backup_heirs=0)
        for row in changed.values():
            row['availability'] = 'known_absent'
            row['value'] = 0
        run('known-absent-exact-integer-zero-not-unknown', changed, {})
        if pins() != expected:
            raise SystemExit('source changed during capture')
        header = {'schema': 'g2.score-state-python-golden/v1', 'machine_id': machine,
            'observed_at_utc': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'source_sha256': expected, 'original_tests_run': result.testsRun, 'original_skips': 0,
            'original_test_methods': selected, 'vector_count': len(vectors), 'packet_json': packets,
            'decimal_default_precision': getcontext().prec, 'native_game_rpc_count': 0,
            'production_consumer_switched': False,
            'scope': ['state_intervals', 'metric', 'bounded_metric', 'state-context relative/bounded_relative/R'],
            'consumers': ['build_report current/baseline states', 'aggregate_state', 'score_ck3_campaign.main'],
            'not_migrated': ['quality_power', 'build_report presentation/date qualification', 'CLI orchestration']}
        for row in [header, *vectors]:
            raw = json.dumps(row, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
            if len(raw) > 65536:
                raise SystemExit('one state vector exceeds default shared parser budget')
            sys.stdout.buffer.write(raw + bytes([10]))
        """;


    public static com.fasterxml.jackson.databind.JsonNode verifyOriginalConsumers() throws Exception {
        return org.xar.ck3.control.wave2.planning.scoretarget.RebellionConsumerGoldenExporter.verifyOriginalConsumer(
                org.xar.ck3.control.wave2.planning.scoretarget.RebellionConsumerGoldenExporter.ConsumerOperation.STATE,
                java.util.List.of(), call -> {
                    var operation = switch (call.operation()) {
                        case REBELLION -> org.xar.ck3.control.contracts.projection.ProjectionOperation.SCORE_REBELLION_PROJECT;
                        case SAVED_MEMBERSHIP -> org.xar.ck3.control.contracts.projection.ProjectionOperation.SAVED_COUNTY_MEMBERSHIP_AUDIT;
                        case STATE -> org.xar.ck3.control.contracts.projection.ProjectionOperation.CAMPAIGN_STATE_SCORE;
                    };
                    var registrations = new java.util.ArrayList<org.xar.ck3.control.contracts.projection.RegisteredProjection>(
                            new org.xar.ck3.control.wave2.planning.scoretarget.SavedScoreProjectionPortCatalog().registrations());
                    registrations.addAll(new ScoreStateProjectionPortCatalog().registrations());
                    var registration = registrations.stream().filter(port -> port.operation() == operation).findFirst().orElseThrow();
                    return org.xar.ck3.control.wave2.planning.scoretarget.RebellionConsumerGoldenExporter.throughRegisteredPort(registration, call.request());
                });
    }

    private StateScoreGoldenExporter() { }
    public static void main(String[] arguments) throws Exception {
        if (arguments.length < 3 || arguments.length > 4) { throw new IllegalArgumentException("repo python machine_id [D-output] required"); }
        Path repo = Path.of(arguments[0]).toAbsolutePath().normalize();
        Path output = arguments.length == 4 ? Path.of(arguments[3]).toAbsolutePath().normalize()
                : repo.resolve("java/ck3-control/wave3-planning/src/test/resources/scorestate/state_python_v1.jsonl");
        if (arguments.length == 4 && !output.getParent().equals(Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1/logs"))) {
            throw new IOException("admitted D logs output required");
        }
        if (Files.exists(output)) { throw new IOException("state golden is create-only"); }
        ProcessBuilder builder = new ProcessBuilder(arguments[1], "-B", "-X", "utf8", "-",
                repo.toString(), arguments[2]).directory(repo.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Path temporary = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize();
        if (!Files.isDirectory(temporary) || !temporary.startsWith(Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1/scratch"))) {
            throw new IOException("admitted D scratch required for original synthetic CLI fixtures");
        }
        builder.environment().put("TEMP", temporary.toString());
        builder.environment().put("TMP", temporary.toString());
        Process process = builder.start();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout = executor.submit(() -> read(process.getInputStream(), 96 * 1024));
            var stderr = executor.submit(() -> read(process.getErrorStream(), 16384));
            try {
                try (var stdin = process.getOutputStream()) {
                    stdin.write(SCRIPT.getBytes(StandardCharsets.UTF_8));
                }
                if (!process.waitFor(90, TimeUnit.SECONDS)) { throw new IOException("state oracle timed out"); }
                byte[] raw = stdout.get(10, TimeUnit.SECONDS); byte[] error = stderr.get(10, TimeUnit.SECONDS);
                System.err.write(error);
                if (process.exitValue() != 0 || raw.length == 0 || raw[raw.length - 1] != 10) {
                    throw new IOException("state oracle failed, exit=" + process.exitValue());
                }
                Files.createDirectories(output.getParent()); Files.write(output, raw, StandardOpenOption.CREATE_NEW);
                System.out.println("WROTE " + output + " bytes=" + raw.length);
            } finally { if (process.isAlive()) { process.destroyForcibly(); } }
        }
    }
    private static byte[] read(InputStream stream, int maximum) throws IOException {
        try (stream; ByteArrayOutputStream output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[8192]; int count;
            while ((count = stream.read(buffer)) != -1) {
                if (output.size() + count > maximum) { throw new IOException("state corpus exceeds finite budget"); }
                output.write(buffer, 0, count);
            }
            return output.toByteArray();
        }
    }
}

