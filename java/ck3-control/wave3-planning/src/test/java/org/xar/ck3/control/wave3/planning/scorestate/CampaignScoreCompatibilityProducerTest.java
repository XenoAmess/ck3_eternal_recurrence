package org.xar.ck3.control.wave3.planning.scorestate;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Set;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.*;
import org.xar.ck3.control.score.projection.CampaignArithmeticProjectionCatalog;

/** Seven named domain reference consumers over a real Java pipe; never current SDK/HTTP qualification. */
final class CampaignScoreCompatibilityProducerTest {
    private static final String SCRIPT = """
        from decimal import Decimal, DecimalException, getcontext, ROUND_UP
        from pathlib import Path
        import hashlib, importlib, importlib.util, json, sys, unittest
        from types import SimpleNamespace
        selection = json.loads(sys.argv[1])
        assert set(selection) == {'schema', 'scope', 'python', 'repository_root', 'candidate', 'reference_client', 'original_sources'}
        assert selection['schema'] == 'xar.score-mechanical-reference-inputs/v1'
        assert selection['scope'] == 'seven-named-score-consumers-reference-only/v1'
        assert sys.flags.isolated == 1 and Path(sys.executable).resolve() == Path(selection['python']).resolve()
        root = Path(selection['repository_root']).resolve(strict=True)
        candidate_ref, client_ref = selection['candidate'], selection['reference_client']
        for row in (candidate_ref, client_ref, *selection['original_sources']):
            assert set(row) == {'path', 'bytes', 'sha256'} and type(row['bytes']) is int and row['bytes'] > 0
            assert Path(row['path']).is_absolute()
        candidate_path, client_path = (Path(row['path']).resolve(strict=True) for row in (candidate_ref, client_ref))
        candidate_sha, client_sha, client_bytes = candidate_ref['sha256'], client_ref['sha256'], client_ref['bytes']
        assert (candidate_ref['bytes'], candidate_sha) == (24703, '65737d5a2082a83fe5c4ab63b057ce6d49f400a54f20bc8b661361acf6c598bf')
        assert (client_bytes, client_sha) == (201161, '0415281fd865bb7e9bbf68175caca2c6ee25a265f194ff5bb623870bea34c970')
        output = sys.stdout
        original_path = root / 'ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py'
        original_sha = 'ba4421fdc66048852e3c7a158a461e8fa2dad5d96c75904e4077e8797652dd4d'
        consumer_pins = {
            'ck3_autonomous_player/tests/unit/test_campaign_development_score_v1.py':
                '0525b7c2e6bd163706b2734b302f3bcad0fd588c50be59e9cbefec458d8c03c2',
            'ck3_autonomous_player/tools/score_ck3_campaign.py':
                'ba6493478872ee6c100360b689d1eed4c8aca6aee40463b44a7bf1b3f849b212',
            'ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py':
                'ffd650323c016b03204517f8ff460f1907ff603057b773372e1c836a74e19b2e',
            'tools/g2_saved_campaign/current_saved_basis_v1.py':
                '6fd69c6bbe958bde489ffe7f391aae690716c26c8ddbe48f82010a5a88261a1e',
            'tools/g2_saved_campaign/file_stat_identity_v1.py':
                'b5c267b11d2b2b7933eec7a62092e29ec2e0d80a8342cab0c7818009385653d0',
            'ck3_autonomous_player/src/xar_autoplayer/ck3_live_run_identity_v1.py':
                'b81c2a1f1e7c562981a1cc001ef65d454a52f4993b2783d3a5a468db84ced43b',
        }
        def sha(path):
            return hashlib.sha256(path.read_bytes()).hexdigest()
        expected_originals = {str(original_path.resolve()): original_sha}
        expected_originals.update((str((root / path).resolve()), digest) for path, digest in consumer_pins.items())
        assert len(selection['original_sources']) == len(expected_originals)
        assert {str(Path(row['path']).resolve()): row['sha256'] for row in selection['original_sources']} == expected_originals
        def verify_selected():
            for row in (candidate_ref, client_ref, *selection['original_sources']):
                path = Path(row['path'])
                assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], path
        verify_selected()
        if client_path.stat().st_size != client_bytes or (sha(original_path), sha(candidate_path), sha(client_path)) != (original_sha, candidate_sha, client_sha):
            raise SystemExit('explicit exact original, candidate and reference-only client required')
        if any(sha(root / path) != digest for path, digest in consumer_pins.items()):
            raise SystemExit('exact unchanged original consumer cohort required')
        sys.path[:0] = [str(root), str(root / 'ck3_autonomous_player/src'), str(root / 'ck3_autonomous_player/tests/unit')]
        def load(name, path):
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            assert Path(module.__file__).resolve() == path.resolve()
            return module
        original = load('xar_autoplayer._unchanged_score_oracle', original_path)
        client = load('tools.g2_saved_campaign.java_map_admission_client_v1', client_path)
        for name, relative in (
            ('tools.g2_saved_campaign.current_saved_basis_v1', 'tools/g2_saved_campaign/current_saved_basis_v1.py'),
            ('tools.g2_saved_campaign.file_stat_identity_v1', 'tools/g2_saved_campaign/file_stat_identity_v1.py')):
            assert Path(sys.modules[name].__file__).resolve() == (root / relative).resolve()
        importlib.import_module('tools.g2_saved_campaign').java_map_admission_client_v1 = client
        fixture_config = object()
        calls = {'campaign-arithmetic-evaluate': 0, 'campaign-state-score': 0}
        provenance_checks = 0
        def interval(row):
            return original.Interval(Decimal(row['lower']), Decimal(row['upper']))
        def expected(operation, packet):
            if operation == 'campaign-state-score':
                return {key: value.export() for key, value in original.state_intervals(packet['current'], packet['baseline']).items()}
            name, value = packet['operation'], packet['input']
            if name == 'aggregate':
                return original.aggregate_state({key: interval(row) for key, row in value.items()}).export()
            if name == 'score360':
                return original.score_360([interval(row) for row in value['samples']], interval(value['endpoint'])).export()
            if name == 'display':
                return original.interval_text(value['lower'], value['upper'], value['places'])
            if name == 'scale':
                return interval(value['interval']).scale(value['weight']).export()
            if name == 'add':
                return interval(value['left']).add(interval(value['right'])).export()
            raise AssertionError('unexpected mechanical operation')
        def exchange(*, operation, payload, request_id):
            assert isinstance(operation, client.ProjectionOperation)
            packet = client.decode_projection_object_v1(payload, maximum_bytes=65536)
            invalid = False
            try:
                wanted = expected(operation.value, packet)
            except (ValueError, TypeError, DecimalException):
                invalid, wanted = True, None
            print(json.dumps({'operation': operation.value, 'call': packet}, ensure_ascii=True,
                separators=(',', ':')), file=output, flush=True)
            message = sys.stdin.buffer.readline(131074)
            assert message and len(message) <= 131073
            response = json.loads(message)
            calls[operation.value] += 1
            if invalid:
                assert response['status'] == 'rejected', response
                raise ValueError('actual Java rejected original invalid arithmetic input')
            assert response['status'] == 'succeeded', response
            assert response['result'] == wanted, (operation.value, response['result'], wanted)
            raw = client.encode_projection_json_v1(response['result'], maximum_bytes=65536)
            return SimpleNamespace(require_success=lambda: raw, result_bytes=raw, payload_bytes=payload,
                request_id=request_id, operation=operation, http_call=None, response_bytes=raw)
        def check(result, *, config, operation, request_id, payload):
            global provenance_checks
            assert config is fixture_config and result.operation is operation
            assert result.request_id == request_id and result.payload_bytes == payload
            provenance_checks += 1
        # This fixture tests the real mechanical wrappers, not shared-client issuance/HTTP qualification.
        client.require_current_projection_config_v1 = lambda: fixture_config
        client.call_current_projection_v1 = exchange
        client.require_result_context_v1 = check
        candidate = load('xar_autoplayer.campaign_development_score_v1', candidate_path)
        import xar_autoplayer
        xar_autoplayer.campaign_development_score_v1 = candidate
        import test_campaign_development_score_v1 as suite
        assert Path(suite.__file__).resolve() == (root / 'ck3_autonomous_player/tests/unit/test_campaign_development_score_v1.py').resolve()
        assert Path(sys.modules['xar_autoplayer.campaign_score_save_reader'].__file__).resolve() == (root / 'ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py').resolve()
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
        if not result.wasSuccessful() or result.testsRun != 7 or result.skipped:
            raise SystemExit('seven named domain reference consumers failed; not a whole/current SDK run')
        assert candidate.Interval.exact('1.25').add(candidate.Interval.exact('2.5')).export() == original.Interval.exact('3.75').export()
        assert candidate.Interval(Decimal('-0'), Decimal('1.0000000000000000000000000000000000000001')).scale('.15').export() == original.Interval(Decimal('-0'), Decimal('1.0000000000000000000000000000000000000001')).scale('.15').export()
        # These are real unchanged original calls through the candidate wrappers.
        # The last two digits deliberately cross the inherited Decimal80 context;
        # neither binary64 nor the ambient Decimal28 context may own these leaves.
        precision_vectors = 0
        for text, weight in (
            ('9007199254740993.0000000000000000000000000000000000000001', '1'),
            ('1.' + '0' * 78 + '05', '1'),
            ('1.' + '0' * 78 + '15', '1'),
            ('9' * 80 + '.5', '1'),
            ('-0', '0.0000001'),
            ('-0E+17', '1E-7'),
            ('1E-100', '1E-100'),
            ('-1234567890123456789012345678901234567890.125', '.15'),
        ):
            assert candidate.Interval.exact(text).scale(weight).export() == original.Interval.exact(text).scale(weight).export()
            precision_vectors += 1
        for left, right in (
            ('9007199254740993.0000000000000000000000000000000000000001', '.0000000000000000000000000000000000000001'),
            ('1.' + '0' * 78 + '05', '0'),
            ('-0', '-0.000'),
            ('123456789012345678901234567890.125', '-123456789012345678901234567890.125'),
        ):
            assert candidate.Interval.exact(left).add(candidate.Interval.exact(right)).export() == original.Interval.exact(left).add(original.Interval.exact(right)).export()
            precision_vectors += 1
        assert precision_vectors == 12
        try:
            candidate.Interval.exact('1').scale('-1')
            raise AssertionError('negative interval weight was accepted')
        except ValueError:
            pass
        old_rounding = getcontext().rounding
        getcontext().rounding = ROUND_UP
        try:
            try:
                candidate.interval_text('1.005', '1.005')
                raise AssertionError('unsupported inherited context was silently mislabeled')
            except ValueError:
                pass
        finally:
            getcontext().rounding = old_rounding
        broken = [
            {'lower': '0', 'upper': '1', 'known': False},
            {'lower': '0', 'upper': '1', 'known': False, 'value': []},
            {'lower': '0', 'upper': '1', 'known': True, 'value': '0'},
            {'lower': 0, 'upper': '1', 'known': False, 'value': None},
            {'lower': '0', 'upper': '1', 'known': False, 'value': None, 'alias': 1},
        ]
        for row in broken:
            raw = client.encode_projection_payload_v1(row, maximum_bytes=65536)
            fixture = SimpleNamespace(require_success=lambda raw=raw: raw, http_call=None, response_bytes=raw)
            try:
                candidate._arithmetic_interval(fixture)
                raise AssertionError('malformed Java interval result was accepted')
            except client.ProjectionUnavailable:
                pass
        if client_path.stat().st_size != client_bytes or (sha(original_path), sha(candidate_path), sha(client_path)) != (original_sha, candidate_sha, client_sha):
            raise SystemExit('original/candidate/client drift during actual consumer test')
        if any(sha(root / path) != digest for path, digest in consumer_pins.items()):
            raise SystemExit('original consumer cohort drift')
        verify_selected()
        assert Path(sys.modules['xar_autoplayer.ck3_live_run_identity_v1'].__file__).resolve() == (root / 'ck3_autonomous_player/src/xar_autoplayer/ck3_live_run_identity_v1.py').resolve()
        assert all(calls.values()) and provenance_checks > 0
        print(json.dumps({'status': 'PASS', 'tests': 7, 'calls': calls, 'fixture_context_checks': provenance_checks,
            'shared_client_issuance_fixture': True, 'actual_http': False, 'malformed_results_rejected': len(broken),
            'source_pre_post': 'MATCH', 'reference_only': True, 'whole_original_suite': False,
            'current_sdk_qualified': False, 'game_rpc_calls': 0, 'selection': selection,
            'decimal_precision_vectors': precision_vectors}, separators=(',', ':')), file=output, flush=True)
        """;

    @Test void actualMechanicalProducerContinuesAllOriginalScoreReportAndCliConsumers() throws Exception {
        var selected = CampaignScoreCompatibilityInputs.fromProperties(System.getProperties());
        selected.verifyActual();
        byte[] recorded = selected.encode();
        assertEquals(selected, CampaignScoreCompatibilityInputs.decode(recorded));
        assertEquals(selected, CampaignScoreCompatibilityInputs.fromProperties(selected.properties()));
        ProcessBuilder builder = new ProcessBuilder(selected.python().toString(), "-B", "-I", "-X", "utf8", "-c", SCRIPT,
                new String(recorded, StandardCharsets.UTF_8)).directory(selected.repository().toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Path temporary = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize();
        assertTrue(Files.isDirectory(temporary), "owned test temporary directory required");
        for (String key : List.of("TEMP", "TMP", "TMPDIR")) { builder.environment().put(key, temporary.toString()); }
        Process process = builder.start();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var error = executor.submit(() -> process.getErrorStream().readNBytes(32769));
            var messages = executor.submit(() -> communicate(process));
            try {
                assertTrue(process.waitFor(100, TimeUnit.SECONDS), "actual mechanical consumer cohort timed out");
                byte[] stderr = error.get(5, TimeUnit.SECONDS); assertTrue(stderr.length <= 32768);
                assertEquals(0, process.exitValue(), new String(stderr, StandardCharsets.UTF_8));
                JsonNode summary = messages.get(5, TimeUnit.SECONDS);
                assertEquals("PASS", StrictJson.text(summary.get("status")));
                assertEquals(7, StrictJson.integer(summary.get("tests"), 7, 7));
                StrictJson.trueValue(summary.get("shared_client_issuance_fixture"));
                falseFlag(summary.get("actual_http"));
                StrictJson.trueValue(summary.get("reference_only"));
                falseFlag(summary.get("whole_original_suite"));
                falseFlag(summary.get("current_sdk_qualified"));
                assertEquals(5, StrictJson.integer(summary.get("malformed_results_rejected"), 5, 5));
                assertEquals("MATCH", StrictJson.text(summary.get("source_pre_post")));
                assertEquals(0, StrictJson.integer(summary.get("game_rpc_calls"), 0, 0));
                assertEquals(12, StrictJson.integer(summary.get("decimal_precision_vectors"), 12, 12));
                assertArrayEquals(recorded, StrictJson.canonical(summary.get("selection")), "actual child must roundtrip the exact selected role metadata");
                StrictJson.object(summary.get("calls"), Set.of("campaign-arithmetic-evaluate", "campaign-state-score"));
                for (String operation : List.of("campaign-arithmetic-evaluate", "campaign-state-score"))
                    assertTrue(StrictJson.integer(summary.get("calls").get(operation), 1, Long.MAX_VALUE) > 0, operation);
                assertTrue(StrictJson.integer(summary.get("fixture_context_checks"), 1, Long.MAX_VALUE) > 0);
                selected.verifyActual();
                System.out.println("MECHANICAL_SCORE_CONSUMERS " + summary);
            } finally { if (process.isAlive()) { process.destroyForcibly(); } }
        }
    }

    private static JsonNode communicate(Process process) throws Exception {
        ProjectionDispatcher dispatcher = ProjectionDispatcher.fromCatalogs(List.of(
                new CampaignArithmeticProjectionCatalog(), new ScoreStateProjectionPortCatalog()));
        JsonNode summary = null;
        try (var input = process.getOutputStream();
                var reader = new BufferedReader(new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = boundedLine(reader)) != null) {
                JsonNode message = StrictJson.parse(line.getBytes(StandardCharsets.UTF_8), 131072);
                assertNull(summary, "summary must be the final child message");
                if (!message.has("call")) {
                    summary = StrictJson.object(message, Set.of("status", "tests", "calls", "fixture_context_checks", "shared_client_issuance_fixture",
                            "actual_http", "malformed_results_rejected", "source_pre_post", "reference_only", "whole_original_suite", "current_sdk_qualified", "game_rpc_calls", "selection", "decimal_precision_vectors"));
                    continue;
                }
                StrictJson.object(message, Set.of("operation", "call"));
                ProjectionOperation operation = ProjectionOperation.fromWire(StrictJson.text(message.get("operation")));
                assertTrue(operation == ProjectionOperation.CAMPAIGN_ARITHMETIC_EVALUATE || operation == ProjectionOperation.CAMPAIGN_STATE_SCORE);
                ProjectionCall call = new ProjectionCall(new ProjectionCall.Identity("mechanical-score-consumer", operation),
                        ProjectionJson.object(StrictJson.canonical(message.get("call")), 65536));
                ProjectionResult result = dispatcher.dispatch(ProjectionWire.encodeCall(call));
                ObjectNode response = StrictJson.object();
                if (result instanceof ProjectionResult.Succeeded succeeded) {
                    response.put("status", "succeeded"); response.set("result", StrictJson.parse(succeeded.result().bytes()));
                } else {
                    ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class, result);
                    response.put("status", "rejected").put("code", rejected.error().code().name());
                }
                input.write(StrictJson.canonical(response)); input.write(10); input.flush();
            }
        } catch (Exception failure) { process.destroyForcibly(); throw failure; }
        assertNotNull(summary); return summary;
    }
    private static String boundedLine(BufferedReader reader) throws IOException {
        StringBuilder line = new StringBuilder();
        for (int value; (value = reader.read()) != -1;) {
            if (value == '\n') return line.toString();
            if (line.length() == 131072) throw new IOException("original score child line exceeded finite contract");
            line.append((char)value);
        }
        if (!line.isEmpty()) throw new IOException("original score child omitted its message terminator");
        return null;
    }
    private static void falseFlag(JsonNode value) { assertTrue(value != null && value.isBoolean() && !value.booleanValue(), "actual JSON false required"); }
}
