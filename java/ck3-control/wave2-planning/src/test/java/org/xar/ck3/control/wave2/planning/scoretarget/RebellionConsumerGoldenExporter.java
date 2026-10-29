package org.xar.ck3.control.wave2.planning.scoretarget;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Capture actual narrow consumer writes from the unchanged _project_metrics call stack. */
public final class RebellionConsumerGoldenExporter {
    private static final String SCRIPT = """
        from copy import deepcopy
        from datetime import datetime, timezone
        import hashlib
        import json
        from pathlib import Path
        import sys
        repo = Path(sys.argv[1]).resolve()
        machine = sys.argv[2]
        sys.path.insert(0, str(repo / 'ck3_autonomous_player/src'))
        from xar_autoplayer import campaign_score_save_reader as reader
        path = 'ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py'
        expected_sha = 'ffd650323c016b03204517f8ff460f1907ff603057b773372e1c836a74e19b2e'
        def pin():
            return hashlib.sha256((repo / path).read_bytes()).hexdigest()
        if pin() != expected_sha or sys.get_int_max_str_digits() != 4300:
            raise SystemExit('qualified unchanged source and integer digit domain required')
        vectors = []
        source = 'synthetic-current-checkpoint'
        original_observation = reader.observation
        def run(case, fields, wars, *, unknown=0, containers=None, layout=False):
            containers = [['wars', 'active_wars']] if containers is None else containers
            request = {'player': {'actor': 3, 'character_fields': deepcopy(fields), 'wars': deepcopy(wars)},
                'unknown_key_fields': unknown, 'war_containers': containers,
                'war_layout_unknown': layout, 'source_ref': source}
            projection = reader.SaveProjection({3})
            projection.characters[3] = deepcopy(fields)
            projection.wars = deepcopy(wars)
            projection.unknown_key_fields = unknown
            projection.war_containers = {tuple(path) for path in containers}
            projection.war_layout_unknown = layout
            projection.stream_complete = True
            projection.root_keys.append('landed_titles')
            projection.metadata['date'] = '1066.10.15'
            writes = []
            def capture_observation(name, value, source, locator, *, reason=None):
                result = original_observation(name, value, source, locator, reason=reason)
                caller = sys._getframe(1)
                if caller.f_code.co_name == '_project_metrics' and 825 <= caller.f_lineno <= 842:
                    writes.append({'metric': name, 'observation': deepcopy(result)})
                return result
            row = {'ordinal': len(vectors) + 1, 'case': case,
                'input_json': json.dumps(request, allow_nan=False, ensure_ascii=False, separators=(',', ':'))}
            reader.observation = capture_observation
            try:
                _, detail, _ = reader.project_metrics(projection, actor=3, founder=3, source_id=source)
            except ValueError:
                row['expected_kind'] = 'invalid_contract'
                vectors.append(row)
                return
            finally:
                reader.observation = original_observation
            if len(writes) > 1:
                raise SystemExit('consumer stage produced unexpected multiple writes')
            row['expected_kind'] = 'result'
            row['expected'] = {'player_war_scope': deepcopy(detail['player_war_scope']),
                'metric_update': writes[0] if writes else None}
            vectors.append(row)
        run('listed-no-defence', {'landed_data.wars': '9'}, {9: {'casus_belli.defender': '7'}})
        run('listed-defending', {'landed_data.wars': '9'}, {9: {'casus_belli.defender': '3'}})
        run('complete-empty-world-roster', {}, {})
        run('complete-world-defending', {}, {9: {'casus_belli.defender': '3'}})
        run('complete-world-unrelated', {}, {9: {'casus_belli.defender': '7'}})
        run('world-shell-is-not-absence', {}, {9: {}})
        run('world-conflict-marker-presence', {}, {9: {'casus_belli.defender': '7', 'nonunique:casus_belli.defender': False}})
        run('unknown-keys-block-listed-metric-write', {'landed_data.wars': '9'}, {9: {'casus_belli.defender': '7'}}, unknown=1)
        run('unknown-keys-block-world-fallback', {}, {}, unknown=1)
        run('unknown-layout-blocks-world-fallback', {}, {}, layout=True)
        run('no-container-blocks-world-fallback', {}, {}, containers=[])
        run('invalid-list-does-not-use-world-fallback', {'landed_data.wars': '9 9'}, {9: {'casus_belli.defender': '7'}})
        run('explicit-empty-list-retains-priority', {'present:landed_data.wars': 'true'}, {9: {'casus_belli.defender': '3'}})
        run('sdk-float-extension-is-not-coerced-or-exact-key-rejected', {'landed_data.wars': '9', 'future': 1.0},
            {9: {'casus_belli.defender': '7', 'future': [None, False]}})
        run('qualified-python-integer-digit-limit', {'landed_data.wars': '1' * 4301}, {})
        if pin() != expected_sha:
            raise SystemExit('source changed while capturing consumer')
        header = {'schema': 'g2.scoretarget-rebellion-consumer-golden/v1', 'machine_id': machine,
            'observed_at_utc': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'source_sha256': {path: expected_sha}, 'vector_count': len(vectors),
            'capture': 'actual_original_project_metrics_and_observation_call_stack_825_842',
            'native_game_rpc_count': 0, 'production_consumer_switched': False}
        for row in [header, *vectors]:
            raw = json.dumps(row, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
            if len(raw) > 65536:
                raise SystemExit('one consumer golden exceeds shared parser')
            sys.stdout.buffer.write(raw + bytes([10]))
        """;

    public enum ConsumerOperation { REBELLION, SAVED_MEMBERSHIP, STATE }
    public record ConsumerRequest(ConsumerOperation operation, byte[] request) {
        public ConsumerRequest {
            java.util.Objects.requireNonNull(operation, "consumer operation");
            java.util.Objects.requireNonNull(request, "consumer request");
            if (request.length == 0 || request.length > 65536) { throw new IllegalArgumentException("unchanged 64 KiB consumer request limit"); }
            request = request.clone();
        }
        @Override public byte[] request() { return request.clone(); }
    }
    private static final int CONSUMER_CARRIER_BYTES = 512 * 1024;
    private static final java.util.Map<String, String> CONSUMER_PINS = java.util.Map.ofEntries(
            java.util.Map.entry("ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py", "f0288b0cea256347471d2dfe8a2c9a7317dfe56dce605616bcf552615a2585a6"),
            java.util.Map.entry("ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py", "e50e27cec8b6d3ef33d86310a8865c0c8d0f6acc325e4e91637f78a538f9eaf4"),
            java.util.Map.entry("ck3_autonomous_player/tools/score_ck3_campaign.py", "89f8adf5e810fdf57792f2560d7789b3417561ca2751c421485560d28e6b1aed"),
            java.util.Map.entry("ck3_autonomous_player/tests/unit/test_campaign_development_score_v1.py", "b1db313b4dde1b52554a1e284d7cfc28b75575ed5e2eb5df352f511e37ee3ee5"),
            java.util.Map.entry("ck3_autonomous_player/tests/unit/test_campaign_score_save_membership_v1.py", "db3c8595021908f58162b51eb0c4b9324a1f98ed8d0e19461741c13e3cd2acf7"),
            java.util.Map.entry("ck3_autonomous_player/src/xar_autoplayer/campaign_score_target_projection.py", "749742086fa8977c2eafa0593801fe4328228a485ebe5f9178006ee823bb0006"),
            java.util.Map.entry("ck3_autonomous_player/src/xar_autoplayer/__init__.py", "9211e760e9bbea5e995c3c81fc9f221ef754598015f21018e37f923d94eca8ab"),
            java.util.Map.entry("ck3_autonomous_player/src/xar_autoplayer/ck3_live_run_identity_v1.py", "b81c2a1f1e7c562981a1cc001ef65d454a52f4993b2783d3a5a468db84ced43b"));

    /** Same test helper and closed UTF-8 stdin transport; no service or extra JVM. */
    public static com.fasterxml.jackson.databind.JsonNode verifyOriginalConsumer(
            ConsumerOperation scenario, java.util.List<String> cases,
            java.util.function.Function<ConsumerRequest, byte[]> evaluator) throws Exception {
        Path repo = requiredEnvironmentPath("XAR_REPO_ROOT");
        Path python = requiredEnvironmentPath("XAR_ORACLE_PYTHON");
        verifyConsumerPins(repo);
        var collect = org.xar.ck3.control.contracts.StrictJson.object();
        collect.put("mode", "collect"); collect.put("scenario", scenario.name());
        var inputs = collect.putArray("cases"); cases.forEach(inputs::add);
        var prepared = runConsumerVerification(repo, python, collect);
        org.xar.ck3.control.contracts.StrictJson.require("PASS".equals(prepared.path("status").textValue()), "actual original consumer collection failed");
        var requests = prepared.get("requests");
        org.xar.ck3.control.contracts.StrictJson.require(requests != null && requests.isArray() && !requests.isEmpty(), "actual consumer requests required");
        var apply = org.xar.ck3.control.contracts.StrictJson.object();
        apply.put("mode", "apply"); apply.put("scenario", scenario.name());
        apply.set("cases", inputs);
        var responses = apply.putArray("responses");
        for (var request : requests) {
            var input = org.xar.ck3.control.contracts.StrictJson.object(request,
                    java.util.Set.of("operation", "request_json"));
            ConsumerOperation operation = ConsumerOperation.valueOf(org.xar.ck3.control.contracts.StrictJson.text(input.get("operation")));
            var carrier = input.get("request_json");
            org.xar.ck3.control.contracts.StrictJson.require(carrier != null && carrier.isTextual(), "raw request carrier required");
            byte[] raw = carrier.textValue().getBytes(StandardCharsets.UTF_8);
            org.xar.ck3.control.contracts.StrictJson.require(raw.length > 0 && raw.length <= 65536, "unchanged per-projection request cap");
            var response = responses.addObject();
            response.put("operation", operation.name()); response.put("request_json", carrier.textValue());
            try {
                byte[] result = evaluator.apply(new ConsumerRequest(operation, raw));
                org.xar.ck3.control.contracts.StrictJson.require(result.length > 0 && result.length <= 65536, "unchanged per-projection response cap");
                response.put("rejected", false);
                response.put("result_json", new String(result, StandardCharsets.UTF_8));
            } catch (IllegalArgumentException rejected) {
                response.put("rejected", true); response.putNull("result_json");
            }
        }
        var result = runConsumerVerification(repo, python, apply);
        verifyConsumerPins(repo);
        org.xar.ck3.control.contracts.StrictJson.require("PASS".equals(result.path("status").textValue())
                && result.path("java_calls").intValue() > 0 && result.path("complete_consumer_comparisons").intValue() > 0,
                "Java output did not pass the complete original consumer");
        return result;
    }

    private static Path requiredEnvironmentPath(String name) throws IOException {
        String value = System.getenv(name);
        if (value == null || value.isBlank()) { throw new IOException("required compatibility consumer environment: " + name); }
        return Path.of(value).toRealPath();
    }

    private static void verifyConsumerPins(Path repo) throws Exception {
        for (var entry : CONSUMER_PINS.entrySet()) {
            Path path = repo.resolve(entry.getKey()).toRealPath();
            if (!path.startsWith(repo) || Files.size(path) > 128 * 1024) { throw new IOException("finite original consumer source required"); }
            String actual = java.util.HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
            if (!actual.equals(entry.getValue())) { throw new IOException("original consumer source mismatch: " + entry.getKey()); }
        }
    }

    private static com.fasterxml.jackson.databind.JsonNode runConsumerVerification(Path repo, Path python,
            com.fasterxml.jackson.databind.node.ObjectNode payload) throws Exception {
        byte[] raw = org.xar.ck3.control.contracts.StrictJson.canonical(payload, CONSUMER_CARRIER_BYTES);
        String script = "import base64,json\n_PAYLOAD=json.loads(base64.b64decode('"
                + java.util.Base64.getEncoder().encodeToString(raw) + "'))\n" + CONSUMER_SCRIPT;
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-B", "-X", "utf8", "-", repo.toString()).directory(repo.toFile());
        Path temporary = Path.of(System.getProperty("java.io.tmpdir")).toAbsolutePath().normalize();
        if (!Files.isDirectory(temporary) || !temporary.startsWith(Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1/scratch"))) {
            throw new IOException("admitted D scratch required for complete original consumer fixtures");
        }
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.environment().put("TEMP", temporary.toString()); builder.environment().put("TMP", temporary.toString());
        Process process = builder.start();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout = executor.submit(() -> read(process.getInputStream(), CONSUMER_CARRIER_BYTES));
            var stderr = executor.submit(() -> read(process.getErrorStream(), 32 * 1024));
            try {
                try (var stdin = process.getOutputStream()) { stdin.write(script.getBytes(StandardCharsets.UTF_8)); }
                if (!process.waitFor(90, TimeUnit.SECONDS)) { throw new IOException("complete original consumer timed out"); }
                byte[] output = stdout.get(10, TimeUnit.SECONDS), error = stderr.get(10, TimeUnit.SECONDS);
                System.err.write(error);
                if (process.exitValue() != 0 || output.length == 0 || output[output.length - 1] != 10) {
                    throw new IOException("complete original consumer failed, exit=" + process.exitValue());
                }
                return org.xar.ck3.control.contracts.StrictJson.parse(output, CONSUMER_CARRIER_BYTES);
            } finally { if (process.isAlive()) { process.destroyForcibly(); } }
        }
    }

    private static final String CONSUMER_SCRIPT = """

        from copy import deepcopy
        from pathlib import Path
        import ast
        import json
        import sys
        import unittest
        from decimal import DecimalException
        repo = Path(sys.argv[1]).resolve()
        sys.path[:0] = [str(repo / 'ck3_autonomous_player/src'), str(repo / 'ck3_autonomous_player/tests/unit')]
        from xar_autoplayer import campaign_score_save_reader as reader
        from xar_autoplayer import campaign_development_score_v1 as scoring
        native_project = reader._project_metrics_oracle
        native_report = scoring._build_report_oracle
        java_project = reader.project_metrics
        java_report = scoring.build_report
        mode, scenario = _PAYLOAD['mode'], _PAYLOAD['scenario']
        requests, seen, calls, comparisons = [], set(), 0, 0
        def key(operation, raw):
            return operation + ':' + scoring.score_request(json.loads(raw)).decode('utf-8')
        responses = {key(row['operation'], row['request_json']): row for row in _PAYLOAD.get('responses', [])}
        def table(rows):
            result = {}
            for token, value in rows.items():
                try:
                    integer = int(token)
                    identity = integer if token == str(integer) else token
                except (ValueError, TypeError):
                    identity = token
                result[identity] = deepcopy(value)
            return result
        def membership_projection(request):
            saved = request['projection']
            projection = reader.SaveProjection({request['actor']})
            titles = table(saved['titles'])
            projection.titles = {identity: titles[identity] for identity in saved['title_order']}
            projection.houses = table(saved['houses'])
            projection.character_houses = table(saved['character_houses'])
            projection.character_house_unknown = set(saved['character_house_unknown'])
            projection.character_sources = set(saved['character_sources'])
            projection.stream_complete = saved['stream_complete']
            projection.unknown_key_fields = saved['unknown_key_fields']
            projection.root_keys = deepcopy(saved['root_keys'])
            projection.metadata = deepcopy(saved['metadata'])
            return projection
        source_lines = Path(reader.__file__).read_text(encoding='utf-8').splitlines()
        war_start = next(index for index, line in enumerate(source_lines, 1)
                         if line.lstrip().startswith('own_defence, war_audit = player_war_defence('))
        war_end = next(index for index, line in enumerate(source_lines, 1)
                       if index > war_start and line.lstrip() == 'if family_unknown:')
        def reference(operation, raw):
            request = json.loads(raw)
            if operation == 'SAVED_MEMBERSHIP':
                projection = membership_projection(request)
                return scoring.score_request(reader._audit_saved_county_membership_v1_oracle(
                    projection, actor=request['actor'], house=request['house'], dynasty=request['dynasty'],
                    county_baronies=request['county_baronies'], source_id=request['source_ref']))
            if operation == 'STATE':
                result = scoring._state_intervals_oracle(request['current'], request['baseline'])
                return scoring.score_request({name: value.export() for name, value in result.items()})
            player = request['player']
            projection = reader.SaveProjection({player['actor']})
            projection.characters[player['actor']] = deepcopy(player['character_fields'])
            projection.wars = table(player['wars'])
            projection.unknown_key_fields = request['unknown_key_fields']
            projection.war_containers = {tuple(path) for path in request['war_containers']}
            projection.war_layout_unknown = request['war_layout_unknown']
            projection.stream_complete = True
            projection.root_keys.append('landed_titles')
            projection.metadata['date'] = '1066.10.15'
            writes = []
            original_observation = reader.observation
            def observe(name, value, source, locator, *, reason=None):
                result = original_observation(name, value, source, locator, reason=reason)
                caller = sys._getframe(1)
                if caller.f_code.co_name == '_project_metrics' and war_start <= caller.f_lineno < war_end:
                    writes.append({'metric': name, 'observation': deepcopy(result)})
                return result
            reader.observation = observe
            try:
                _, detail, _ = native_project(projection, actor=player['actor'], founder=player['actor'],
                    source_id=request['source_ref'])
            finally:
                reader.observation = original_observation
            if len(writes) > 1:
                raise AssertionError('actual legacy consumer produced multiple war writes')
            return scoring.score_request({'player_war_scope': detail['player_war_scope'],
                                          'metric_update': writes[0] if writes else None})
        def invoke(operation, raw):
            global calls
            calls += 1
            token = key(operation, raw)
            if mode == 'collect':
                if token not in seen:
                    requests.append({'operation': operation, 'request_json': raw.decode('utf-8')})
                    seen.add(token)
                return reference(operation, raw)
            if token not in responses:
                raise AssertionError('Java consumer response is missing for the exact typed request')
            row = responses[token]
            if row['rejected']:
                raise ValueError('Java projection rejected the original contract')
            return row['result_json'].encode('utf-8')
        ports = scoring.ScoreConsumerPorts(
            rebellion=lambda raw: invoke('REBELLION', raw),
            saved_membership=lambda raw: invoke('SAVED_MEMBERSHIP', raw),
            state=(lambda raw: invoke('STATE', raw)) if scenario == 'STATE' else None)
        def project(*args, **kwargs):
            global comparisons
            kwargs.pop('consumer_ports', None)
            if mode == 'apply':
                expected = native_project(*deepcopy(args), **deepcopy(kwargs))
            actual = java_project(*args, **kwargs, consumer_ports=ports)
            if mode == 'apply':
                if scoring.score_request(expected) != scoring.score_request(actual):
                    raise AssertionError('Java result changed the complete original project_metrics return')
                comparisons += 1
            return actual
        def report(*args, **kwargs):
            global comparisons
            kwargs.pop('consumer_ports', None)
            if mode == 'apply':
                expected = native_report(*deepcopy(args), **deepcopy(kwargs))
            actual = java_report(*deepcopy(args), **deepcopy(kwargs), consumer_ports=ports)
            if mode == 'apply':
                if scoring.score_request(expected) != scoring.score_request(actual):
                    raise AssertionError('Java result changed the complete original build_report return')
                comparisons += 1
            return actual
        reader.project_metrics = project
        scoring.build_report = report
        if scenario == 'REBELLION':
            tests = 0
            for raw in _PAYLOAD['cases']:
                request = json.loads(raw)
                player = request['player']
                projection = reader.SaveProjection({player['actor']})
                projection.characters[player['actor']] = deepcopy(player['character_fields'])
                projection.wars = table(player['wars'])
                projection.unknown_key_fields = request['unknown_key_fields']
                projection.war_containers = {tuple(path) for path in request['war_containers']}
                projection.war_layout_unknown = request['war_layout_unknown']
                projection.stream_complete = True
                projection.root_keys.append('landed_titles')
                projection.metadata['date'] = '1066.10.15'
                try:
                    project(projection, actor=player['actor'], founder=player['actor'], source_id=request['source_ref'])
                except (ValueError, TypeError, AttributeError, KeyError, DecimalException):
                    if mode == 'apply':
                        try:
                            native_project(projection, actor=player['actor'], founder=player['actor'],
                                source_id=request['source_ref'])
                        except (ValueError, TypeError, AttributeError, KeyError, DecimalException):
                            pass
                        else:
                            raise AssertionError('Java rejected a valid original consumer request')
                    continue
                tests += 1
        else:
            if scenario == 'SAVED_MEMBERSHIP':
                import test_campaign_score_save_membership_v1 as fixture
                fixture.project_metrics = project
                suite = unittest.defaultTestLoader.loadTestsFromTestCase(fixture.SavedCountyMembershipTests)
                required = 11
            else:
                import test_campaign_development_score_v1 as fixture
                fixture.build_report = report
                fixture.state_intervals = lambda current, baseline: scoring.report_state_intervals(current, baseline, ports)
                selected = [
                    'test_missing_baseline_is_interval_and_no_weight_redistribution',
                    'test_debt_rescue_and_lost_half_reproduce_design',
                    'test_exported_repeating_decimals_have_exact_weighted_sum',
                    'test_interval_display_outwards_and_partial_contribution_not_reweighted',
                    'test_complete_explanations_negative_cash_and_strict_date',
                    'test_cli_main_single_projection_scan_auto_map_and_export']
                cases = [fixture.CampaignScoreTests(name) for name in selected]
                for case in cases:
                    case.consumer_ports = ports
                suite = unittest.TestSuite(cases)
                required = 6
            result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
            if not result.wasSuccessful() or result.testsRun != required or result.skipped:
                raise AssertionError('complete original consumer suite failed or skipped')
            tests = result.testsRun
            if scenario == 'STATE':
                additional = unittest.TestSuite(fixture.CampaignScoreTests(name) for name in [
                    'test_java_score_cli_requires_current_configuration_before_source_read',
                    'test_java_score_state_response_contract_and_failure_do_not_use_oracle'])
                extra = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(additional)
                if not extra.wasSuccessful() or extra.testsRun != 2 or extra.skipped:
                    raise AssertionError('new exact consumer boundary regressions failed or skipped')
        if calls == 0 or (mode == 'apply' and comparisons == 0):
            raise AssertionError('actual Java consumer path did not execute')
        output = {'status': 'PASS', 'mode': mode, 'tests': tests, 'java_calls': calls,
                  'complete_consumer_comparisons': comparisons, 'requests': requests}
        encoded = json.dumps(output, ensure_ascii=False, allow_nan=False, sort_keys=True,
                             separators=(',', ':')).encode('utf-8')
        if len(encoded) > 524288:
            raise AssertionError('explicit consumer verification carrier exceeds 512 KiB')
        sys.stdout.buffer.write(encoded + bytes([10]))

        """;


    public static org.xar.ck3.control.contracts.projection.ProjectionResult registeredResult(
            org.xar.ck3.control.contracts.projection.RegisteredProjection registration, byte[] raw) {
        var call = new org.xar.ck3.control.contracts.projection.ProjectionCall(
                new org.xar.ck3.control.contracts.projection.ProjectionCall.Identity(
                        "consumer-" + registration.operation().wire(), registration.operation()),
                org.xar.ck3.control.contracts.projection.ProjectionJson.object(raw, 65536));
        var decoded = org.xar.ck3.control.contracts.projection.ProjectionWire.decodeCall(
                org.xar.ck3.control.contracts.projection.ProjectionWire.encodeCall(call));
        return registration.execute(decoded);
    }

    public static byte[] throughRegisteredPort(
            org.xar.ck3.control.contracts.projection.RegisteredProjection registration, byte[] raw) {
        var result = registeredResult(registration, raw);
        if (result instanceof org.xar.ck3.control.contracts.projection.ProjectionResult.Succeeded succeeded) {
            return succeeded.result().bytes();
        }
        if (result instanceof org.xar.ck3.control.contracts.projection.ProjectionResult.Rejected rejected) {
            if (rejected.error().code() == org.xar.ck3.control.contracts.projection.ProjectionError.Code.DOMAIN_REJECTED
                    || rejected.error().code() == org.xar.ck3.control.contracts.projection.ProjectionError.Code.INVALID_PAYLOAD) {
                throw new IllegalArgumentException(rejected.error().message());
            }
            throw new IllegalStateException("registered consumer projection failed: " + rejected.error().code());
        }
        throw new IllegalStateException("unsupported registered consumer result");
    }

    public static byte[] throughSavedScorePort(ConsumerRequest call) {
        var operation = switch (call.operation()) {
            case REBELLION -> org.xar.ck3.control.contracts.projection.ProjectionOperation.SCORE_REBELLION_PROJECT;
            case SAVED_MEMBERSHIP -> org.xar.ck3.control.contracts.projection.ProjectionOperation.SAVED_COUNTY_MEMBERSHIP_AUDIT;
            case STATE -> throw new IllegalArgumentException("state operation requires the wave3 catalog");
        };
        var registration = new SavedScoreProjectionPortCatalog().registrations().stream()
                .filter(port -> port.operation() == operation).findFirst().orElseThrow();
        return throughRegisteredPort(registration, call.request());
    }

    public static com.fasterxml.jackson.databind.JsonNode verifyOriginalConsumers(java.util.List<String> cases) throws Exception {
        return verifyOriginalConsumer(ConsumerOperation.REBELLION, cases, RebellionConsumerGoldenExporter::throughSavedScorePort);
    }

    /** Source-qualified fixture carrier; legacy capture and current same-host comparison use distinct processes. */
    public static String sameHostConsumerPython() {
        return """
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            from pathlib import Path
            from tools.g2_saved_campaign.current_saved_basis_v1 import ExactRefV1
            from tools.g2_saved_campaign.java_map_admission_client_v1 import JavaProjectionServiceV1
            from xar_autoplayer.campaign_development_score_v1 import ScoreConsumerPorts
        
        def _score_fixture_ref_v2(reference: "ExactRefV1 | dict[str, object]") -> tuple[dict[str, object], bytes]:
            from pathlib import Path
            import hashlib
            row = reference if isinstance(reference, dict) else {
                name: getattr(reference, name, None) for name in ("path", "bytes", "sha256")}
            if (set(row) != {"path", "bytes", "sha256"} or not isinstance(row["path"], str)
                    or type(row["bytes"]) is not int or not 1 <= row["bytes"] <= 2097152
                    or not isinstance(row["sha256"], str) or len(row["sha256"]) != 64):
                raise ValueError("exact original capture/source reference required")
            path = Path(row["path"]).resolve(strict=True)
            with path.open("rb") as stream:
                raw = stream.read(2097153)
            if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
                raise ValueError("original capture/source bytes changed")
            return row, raw
        
        def _score_original_modules_v2(*, repository: "Path", module_paths: dict[str, str], fixture_root: "Path",
                fixture_time: str, expected: dict[str, object] | None,
                ports: "ScoreConsumerPorts | None") -> dict[str, object]:
            from pathlib import Path
            from contextlib import ExitStack
            from decimal import Decimal, DecimalException
            from unittest.mock import patch
            from typing import Callable
            import base64, hashlib, importlib, io, json, math, sys, tempfile, unittest
            root, temporary = Path(repository).resolve(strict=True), Path(fixture_root).resolve(strict=True)
            if temporary.is_relative_to(root):
                raise ValueError("fixture metadata must stay outside source view")
            loader = unittest.TestLoader()
            modules = []
            for relative in ("ck3_autonomous_player/tests/unit/test_campaign_development_score_v1.py",
                    "ck3_autonomous_player/tests/unit/test_campaign_score_save_membership_v1.py"):
                path = Path(module_paths[relative]).resolve(strict=True)
                name = path.stem
                module = sys.modules.get(name)
                if module is None:
                    spec = importlib.util.spec_from_file_location(name, path)
                    if spec is None or spec.loader is None:
                        raise ValueError("qualified full test module loader unavailable")
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[name] = module
                    spec.loader.exec_module(module)
                if Path(module.__file__).resolve(strict=True) != path:
                    raise ValueError("full score module selected another physical source")
                modules.append(module)
            score_tests, member_tests = modules
            suite = unittest.TestSuite(loader.loadTestsFromModule(module) for module in modules)
            required_tests = suite.countTestCases()
            if expected is None and required_tests != 29:
                raise ValueError("all original 18 + 11 test methods required")
            from xar_autoplayer import campaign_development_score_v1 as scoring
            from xar_autoplayer import campaign_score_save_reader as reader
            if expected is None and (hasattr(scoring, "java_score_consumer_ports")
                    or hasattr(reader, "_project_metrics_oracle")):
                raise ValueError("original baseline must execute the separate unchanged legacy view")
            client = None
            if expected is not None:
                from tools.g2_saved_campaign import java_map_admission_client_v1 as client
            source_pins = []
            if expected is None:
                from xar_autoplayer import campaign_score_target_projection as target
                original = {
                    "ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py": "ba4421fdc66048852e3c7a158a461e8fa2dad5d96c75904e4077e8797652dd4d",
                    "ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py": "ffd650323c016b03204517f8ff460f1907ff603057b773372e1c836a74e19b2e",
                    "ck3_autonomous_player/tools/score_ck3_campaign.py": "ba6493478872ee6c100360b689d1eed4c8aca6aee40463b44a7bf1b3f849b212",
                    "ck3_autonomous_player/tests/unit/test_campaign_development_score_v1.py": "0525b7c2e6bd163706b2734b302f3bcad0fd588c50be59e9cbefec458d8c03c2",
                    "ck3_autonomous_player/tests/unit/test_campaign_score_save_membership_v1.py": "db3c8595021908f58162b51eb0c4b9324a1f98ed8d0e19461741c13e3cd2acf7",
                    "ck3_autonomous_player/src/xar_autoplayer/campaign_score_target_projection.py": "749742086fa8977c2eafa0593801fe4328228a485ebe5f9178006ee823bb0006",
                    "ck3_autonomous_player/src/xar_autoplayer/__init__.py": "9211e760e9bbea5e995c3c81fc9f221ef754598015f21018e37f923d94eca8ab",
                    "ck3_autonomous_player/src/xar_autoplayer/ck3_live_run_identity_v1.py": "b81c2a1f1e7c562981a1cc001ef65d454a52f4993b2783d3a5a468db84ced43b",
                }
                actual_modules = {
                    "ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py": scoring,
                    "ck3_autonomous_player/src/xar_autoplayer/campaign_score_save_reader.py": reader,
                    "ck3_autonomous_player/src/xar_autoplayer/campaign_score_target_projection.py": target,
                    "ck3_autonomous_player/tests/unit/test_campaign_development_score_v1.py": score_tests,
                    "ck3_autonomous_player/tests/unit/test_campaign_score_save_membership_v1.py": member_tests,
                }
                for relative, digest in original.items():
                    path = (Path(actual_modules[relative].__file__) if relative in actual_modules else root / relative).resolve(strict=True)
                    data = path.read_bytes()
                    if hashlib.sha256(data).hexdigest() != digest:
                        raise ValueError("legacy consumer source differs from original input: " + relative)
                    source_pins.append({"path": str(path), "bytes": len(data), "sha256": digest})
            rows, methods, temp_paths, terminal_files = [], [], [], []
            wanted = {} if expected is None else {
                (row["test"], row["consumer"], row["ordinal"]): row for row in expected["returns"]}
            expected_paths = [] if expected is None else expected["temporary_directories"]
            expected_files = {} if expected is None else {
                (row["test"], row["path"]): row for row in expected["terminal_files"]}
            consumed, consumed_files = set(), set()
            current, depth, ordinal = None, 0, {}
            comparisons, rejection_comparisons, extra_checks = 0, 0, 0
            def normalize(value: object) -> object:
                if isinstance(value, scoring.Interval):
                    return normalize(value.export())
                if value is None or type(value) in (bool, int, str):
                    if isinstance(value, str):
                        value.encode("utf-8", errors="strict")
                    return value
                if isinstance(value, Decimal):
                    if not value.is_finite():
                        raise ValueError("nonfinite original return")
                    return str(value)
                if isinstance(value, float):
                    if not math.isfinite(value):
                        raise ValueError("nonfinite original return")
                    return value
                if isinstance(value, (list, tuple)):
                    return [normalize(item) for item in value]
                if isinstance(value, dict):
                    result = {}
                    for key, item in value.items():
                        if not isinstance(key, str) and type(key) is not int:
                            raise ValueError("original JSON key type differs")
                        token = str(key)
                        if token in result:
                            raise ValueError("original JSON key collision")
                        result[token] = normalize(item)
                    return result
                raise ValueError("original return is outside its JSON contract")
            def packed(value: object) -> str:
                raw = json.dumps(normalize(value), ensure_ascii=False, allow_nan=False,
                    sort_keys=True, separators=(",", ":")).encode("utf-8")
                if len(raw) > 65536:
                    raise ValueError("one complete consumer return exceeds explicit 64 KiB fixture cap")
                return raw.decode("utf-8")
            def consume(name: str, function: Callable[..., object], args: tuple[object, ...], kwargs: dict[str, object]) -> object:
                nonlocal depth, comparisons, rejection_comparisons, extra_checks
                if depth:
                    return function(*args, **kwargs)
                if current is None:
                    raise ValueError("consumer ran outside an original test method")
                key = (current, name)
                ordinal[key] = ordinal.get(key, 0) + 1
                identity = (current, name, ordinal[key])
                previous = wanted.get(identity)
                depth += 1
                try:
                    try:
                        value = function(*args, **kwargs)
                    except (ValueError, TypeError, AttributeError, KeyError, DecimalException) as failure:
                        if client is not None and isinstance(failure, client.ProjectionUnavailable):
                            if not isinstance(failure, client.ProjectionDomainRejected):
                                raise
                        row = {"test": current, "consumer": name, "ordinal": identity[2],
                            "kind": "rejected", "error_class": type(failure).__name__, "value_json": None}
                        if previous is not None:
                            if previous["kind"] != "rejected":
                                raise AssertionError("Java rejected a complete original successful return") from failure
                            if not (client is not None and isinstance(failure, client.ProjectionDomainRejected)):
                                if type(failure).__name__ != previous["error_class"]:
                                    raise AssertionError("original local rejection category changed") from failure
                            rejection_comparisons += 1
                            consumed.add(identity)
                        elif expected is not None:
                            if current in expected["test_methods"]:
                                raise AssertionError("unrecorded original consumer rejection") from failure
                            extra_checks += 1
                        rows.append(row)
                        raise
                    row = {"test": current, "consumer": name, "ordinal": identity[2],
                        "kind": "returned", "error_class": None, "value_json": packed(value)}
                    if previous is not None:
                        if previous["kind"] != "returned" or previous["value_json"] != row["value_json"]:
                            raise AssertionError("complete original consumer return differs: " + str(identity))
                        comparisons += 1
                        consumed.add(identity)
                    elif expected is not None:
                        if current in expected["test_methods"]:
                            raise AssertionError("unrecorded original consumer return")
                        extra_checks += 1
                    rows.append(row)
                    return value
                finally:
                    depth -= 1
            native_state, native_report, native_project = scoring.state_intervals, scoring.build_report, reader.project_metrics
            def state(*args: object, **kwargs: object) -> object:
                if ports is not None and kwargs.get("consumer_ports") is None:
                    kwargs["consumer_ports"] = ports
                return consume("state_intervals", native_state, args, kwargs)
            def report(*args: object, **kwargs: object) -> object:
                if ports is not None and kwargs.get("consumer_ports") is None:
                    kwargs["consumer_ports"] = ports
                return consume("build_report", native_report, args, kwargs)
            def project(*args: object, **kwargs: object) -> object:
                if ports is not None and kwargs.get("consumer_ports") is None:
                    kwargs["consumer_ports"] = ports
                return consume("project_metrics", native_project, args, kwargs)
            real_mkdtemp, real_cleanup = tempfile.mkdtemp, tempfile.TemporaryDirectory.cleanup
            def mkdtemp(suffix: str | None = None, prefix: str | None = None, dir: object = None) -> str:
                if dir is not None and Path(dir).resolve(strict=True) != temporary:
                    raise ValueError("unexpected original fixture directory")
                if expected is None:
                    path = Path(real_mkdtemp(suffix=suffix, prefix=prefix, dir=str(temporary)))
                else:
                    index = len(temp_paths)
                    if index >= len(expected_paths):
                        raise ValueError("unrecorded original temporary directory")
                    record = expected_paths[index]
                    if record["test"] != current or record["prefix"] != prefix or record["suffix"] != suffix:
                        raise ValueError("original temporary directory sequence differs")
                    path = Path(record["path"])
                    if path.parent.resolve(strict=True) != temporary:
                        raise ValueError("original fixture path escaped admitted shared scratch")
                    path.mkdir(exist_ok=False)
                temp_paths.append({"test": current, "path": str(path), "prefix": prefix, "suffix": suffix})
                return str(path)
            def cleanup(directory: object) -> None:
                base = Path(directory.name).resolve(strict=True)
                if base.parent != temporary:
                    raise ValueError("original fixture cleanup escaped admitted scratch")
                try:
                    for path in sorted(base.rglob("*")):
                        if not path.is_file():
                            continue
                        raw = path.read_bytes()
                        if len(raw) > 65536:
                            raise ValueError("one original fixture terminal exceeds 64 KiB")
                        row = {"test": current, "path": str(path), "bytes": len(raw),
                            "raw_base64": base64.b64encode(raw).decode("ascii")}
                        key = (current, str(path))
                        if expected is not None:
                            previous = expected_files.get(key)
                            if previous != row:
                                raise AssertionError("complete original CLI/fixture file differs: " + str(path))
                            consumed_files.add(key)
                        terminal_files.append(row)
                finally:
                    real_cleanup(directory)
            class CompleteOriginalResult(unittest.TextTestResult):
                def startTest(self, test: unittest.TestCase) -> None:
                    nonlocal current
                    current = type(test).__name__ + "." + test._testMethodName
                    methods.append(current)
                    super().startTest(test)
                def stopTest(self, test: unittest.TestCase) -> None:
                    nonlocal current
                    super().stopTest(test)
                    current = None
            with ExitStack() as stack:
                for module, symbol, replacement in (
                        (scoring, "state_intervals", state), (scoring, "build_report", report),
                        (reader, "project_metrics", project), (score_tests, "state_intervals", state),
                        (score_tests, "build_report", report), (member_tests, "project_metrics", project)):
                    stack.enter_context(patch.object(module, symbol, replacement))
                stack.enter_context(patch.object(reader, "utc", return_value=fixture_time))
                stack.enter_context(patch.object(tempfile, "mkdtemp", mkdtemp))
                stack.enter_context(patch.object(tempfile.TemporaryDirectory, "cleanup", cleanup))
                run = unittest.TextTestRunner(verbosity=2, resultclass=CompleteOriginalResult).run(suite)
            if run.testsRun != required_tests or run.testsRun < 1 or not run.wasSuccessful() or run.skipped or run.expectedFailures or run.unexpectedSuccesses:
                raise ValueError("complete original score modules failed/empty/skipped")
            if not rows or not terminal_files:
                raise ValueError("original full consumer/CLI paths did not execute")
            if expected is not None and (consumed != set(wanted) or consumed_files != set(expected_files)
                    or len(temp_paths) != len(expected_paths) or not set(expected["test_methods"]).issubset(methods)):
                raise ValueError("not every complete original consumer/CLI return was consumed")
            for reference in source_pins:
                _score_fixture_ref_v2(reference)
            return {"returns": rows, "test_methods": methods, "tests_run": run.testsRun,
                "original_sources": source_pins,
                "temporary_directories": temp_paths, "terminal_files": terminal_files,
                "complete_return_comparisons": comparisons, "rejection_comparisons": rejection_comparisons,
                "additional_current_checks": extra_checks}
        
        def capture_score_original_consumers_v1(*, legacy_actual_ref: "ExactRefV1",
                fixture_root: "Path", output: "Path") -> dict[str, object]:
            from pathlib import Path
            from datetime import datetime, timezone
            import gzip, hashlib, json
            legacy_ref, graph_raw = _score_fixture_ref_v2(legacy_actual_ref)
            graph = json.loads(graph_raw)
            if graph["schema"] != "xar.sdk-source-assembly-actual/v1" or graph["status"] != "SOURCE_ASSEMBLED_NOT_IMPORTED":
                raise ValueError("source-qualified separate legacy actual required")
            repository = Path(graph["canonical_test_repository"]).resolve(strict=True)
            destination, temporary = Path(output).absolute(), Path(fixture_root).resolve(strict=True)
            if destination.parent.resolve(strict=True) != temporary or destination.exists():
                raise ValueError("create-only admitted original baseline output required")
            fixture_time = datetime.now(timezone.utc).isoformat()
            module_paths = {row["relative_source"]: row["physical_ref"]["path"] for row in graph["selected_import_routes"]}
            result = _score_original_modules_v2(repository=repository, module_paths=module_paths, fixture_root=temporary,
                fixture_time=fixture_time, expected=None, ports=None)
            result.update({"schema": "xar.score-original-complete-consumers/v1", "machine_id": graph["machine_id"],
                "legacy_actual_ref": legacy_ref, "fixture_root": str(temporary), "fixture_time": fixture_time})
            raw = json.dumps(result, ensure_ascii=False, allow_nan=False,
                separators=(",", ":"), sort_keys=True).encode("utf-8")
            if len(raw) > 1048576:
                raise ValueError("original complete consumer baseline exceeds 1 MiB decoded fixture cap")
            compressed = gzip.compress(raw, mtime=0)
            if len(compressed) > 131072:
                raise ValueError("original baseline exceeds 128 KiB compressed artifact cap")
            _score_fixture_ref_v2(legacy_actual_ref)
            with destination.open("xb") as stream:
                stream.write(compressed)
            reference = {"path": str(destination), "bytes": len(compressed),
                "sha256": hashlib.sha256(compressed).hexdigest()}
            return {"status": "PASS", "baseline_ref": reference, "legacy_actual_ref": legacy_ref,
                "complete_modules": 2, "tests_run": result["tests_run"],
                "complete_returns": len(result["returns"]), "terminal_files": len(result["terminal_files"]),
                "actual_projection_http": False}
        
        def run_score_java_consumers_v1(*, config: "JavaProjectionServiceV1", shared_views_ref: "ExactRefV1",
                baseline_actual_ref: "ExactRefV1", baseline_ref: "ExactRefV1", fixture_root: "Path") -> dict[str, object]:
            from pathlib import Path
            import gzip, io, json
            from tools.g2_saved_campaign import java_map_admission_client_v1 as client
            from xar_autoplayer import campaign_development_score_v1 as scoring
            views_ref, views_raw = _score_fixture_ref_v2(shared_views_ref)
            capture_ref, capture_raw = _score_fixture_ref_v2(baseline_actual_ref)
            original_ref, compressed = _score_fixture_ref_v2(baseline_ref)
            views, captured = json.loads(views_raw), json.loads(capture_raw)
            def same(one: dict[str, object], two: dict[str, object]) -> bool:
                return (Path(one["path"]).resolve(strict=True) == Path(two["path"]).resolve(strict=True)
                    and one["bytes"] == two["bytes"] and one["sha256"] == two["sha256"])
            if (views["schema"] != "xar.sdk-shared-source-views-actual/v1"
                    or captured["schema"] != "xar.shared-golden-capture-actual/v1"
                    or captured["status"] != "PASS" or captured["source_unchanged"] is not True
                    or captured["error"] is not None or captured["result"]["exit_code"] != 0
                    or captured["result"]["accounting"]["active_processes"] != 0
                    or not same(captured["output_ref"], original_ref)
                    or not any(same(row, views["legacy_actual_ref"]) for row in captured["request"]["input_refs"])
                    or not any(same(row, views_ref) for row in captured["request"]["input_refs"])):
                raise ValueError("actual original capture must consume the exact qualified legacy view")
            with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
                raw = stream.read(1048577)
            if len(raw) > 1048576:
                raise ValueError("original complete consumer baseline inflate cap exceeded")
            baseline = json.loads(raw)
            if (baseline["schema"] != "xar.score-original-complete-consumers/v1"
                    or not same(baseline["legacy_actual_ref"], views["legacy_actual_ref"])
                    or Path(baseline["fixture_root"]).resolve(strict=True) != Path(fixture_root).resolve(strict=True)
                    or not isinstance(config, client.JavaProjectionServiceV1)
                    or client.require_current_projection_config_v1() is not config or config.transport is not None
                    or baseline["machine_id"] != config.machine_id or views["machine_id"] != config.machine_id
                    or captured["machine_id"] != config.machine_id):
                raise client.ProjectionUnavailable("same installed configuration and original capture custody required")
            if len(baseline["test_methods"]) != 29:
                raise ValueError("complete original 18 + 11 test baseline required")
            for reference in baseline["original_sources"]:
                _score_fixture_ref_v2(reference)
            _, consumer_raw = _score_fixture_ref_v2(views["consumer_actual_ref"])
            consumer = json.loads(consumer_raw)
            identity = client.qualify_projection_service_v1(config)
            if not identity.actual_http:
                raise client.ProjectionUnavailable("actual same-host stdlib HTTP required")
            for operation in (client.ProjectionOperation.SCORE_REBELLION_PROJECT,
                    client.ProjectionOperation.SAVED_COUNTY_MEMBERSHIP_AUDIT,
                    client.ProjectionOperation.CAMPAIGN_STATE_SCORE):
                profile = identity.profile(operation)
                if profile.input_max_bytes != 65536 or profile.output_max_bytes != 65536:
                    raise client.ProjectionUnavailable("unchanged score operation profile required")
            evidence = []
            ports = scoring.java_score_consumer_ports(config=config, evidence_sink=evidence.append)
            module_paths = {row["relative_source"]: row["physical_ref"]["path"] for row in consumer["selected_import_routes"]}
            result = _score_original_modules_v2(repository=consumer["canonical_test_repository"], module_paths=module_paths,
                fixture_root=fixture_root, fixture_time=baseline["fixture_time"], expected=baseline, ports=ports)
            if not evidence or any(not row.actual_http_invoked or row.transport_kind != "stdlib-http-loopback/v1"
                    or row.identity_sha256 != identity.identity_sha256 for row in evidence):
                raise client.ProjectionUnavailable("complete consumer calls did not retain actual same-host evidence")
            before = len(evidence)
            try:
                ports.required("state")(scoring.score_request({"current": {"rebel_share": {
                    "availability": "observed", "unit": "fraction", "value": "2"}}, "baseline": {}}))
            except client.ProjectionDomainRejected as rejection:
                if (rejection.code != "domain-rejected" or not isinstance(rejection, ValueError) or rejection.http_call is None
                        or not rejection.http_call.actual_http_invoked or len(evidence) != before + 1):
                    raise AssertionError("verified domain rejection lost its actual HTTP evidence") from rejection
            else:
                raise AssertionError("actual invalid scoring input was not rejected by its typed validator")
            final = client.qualify_projection_service_v1(config)
            if final.identity_sha256 != identity.identity_sha256 or final.process != identity.process:
                raise client.ProjectionUnavailable("same-host process/source/profile changed during full consumers")
            for ref in (shared_views_ref, baseline_actual_ref, baseline_ref):
                _score_fixture_ref_v2(ref)
            return {"status": "PASS", "complete_modules": 2, "tests_run": result["tests_run"],
                "complete_return_comparisons": result["complete_return_comparisons"],
                "rejection_comparisons": result["rejection_comparisons"],
                "complete_cli_files_compared": len(baseline["terminal_files"]),
                "same_installed_configuration": True, "verified_domain_rejection": True,
                "issued_result_context_scope": "shared factory require_result_context plus sole CI issued observer",
                "legacy_capture_ref": capture_ref, "shared_views_ref": views_ref}
        
        """;
    }

    private RebellionConsumerGoldenExporter() { }

    public static void main(String[] arguments) throws Exception {
        if (arguments.length < 3 || arguments.length > 4) { throw new IllegalArgumentException("repo python machine_id [D-output] required"); }
        Path repo = Path.of(arguments[0]).toAbsolutePath().normalize();
        Path output = arguments.length == 4 ? Path.of(arguments[3]).toAbsolutePath().normalize()
                : repo.resolve("java/ck3-control/wave2-planning/src/test/resources/scoretarget/rebellion_consumer_python_v1.jsonl");
        if (arguments.length == 4 && !output.getParent().equals(Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1/logs"))) {
            throw new IOException("admitted D logs output required");
        }
        if (Files.exists(output)) { throw new IOException("create-only consumer golden already exists"); }
        Process process = new ProcessBuilder(arguments[1], "-B", "-X", "utf8", "-",
                repo.toString(), arguments[2]).directory(repo.toFile()).start();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout = executor.submit(() -> read(process.getInputStream(), 24 * 1024));
            var stderr = executor.submit(() -> read(process.getErrorStream(), 8192));
            try {
                try (var stdin = process.getOutputStream()) {
                    stdin.write(SCRIPT.getBytes(StandardCharsets.UTF_8));
                }
                if (!process.waitFor(90, TimeUnit.SECONDS)) { throw new IOException("consumer oracle timed out"); }
                byte[] raw = stdout.get(10, TimeUnit.SECONDS); byte[] error = stderr.get(10, TimeUnit.SECONDS);
                System.err.write(error);
                if (process.exitValue() != 0 || raw.length == 0 || raw[raw.length - 1] != 10) {
                    throw new IOException("consumer oracle failed, exit=" + process.exitValue());
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
                if (output.size() + count > maximum) { throw new IOException("consumer oracle output exceeds budget"); }
                output.write(buffer, 0, count);
            }
            return output.toByteArray();
        }
    }
}

