package org.xar.ck3.control.nativebridge.capabilities.governance;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;

/** Unchanged actual Python producer/service/MCP tests plus direct producer differential. */
final class DevelopmentStewardOriginalProducerTest {
    private static final String SCRIPT = """
            import contextlib
            import copy
            import dataclasses
            import hashlib
            import importlib.util
            import json
            from pathlib import Path
            import sys
            import unittest
            repo = Path(sys.argv[1]).resolve()
            paths = {
                'ck3_autonomous_player/src/xar_autoplayer/bridge/service.py': 'a8ebc680c41732a567eb1df2831fe210d7b0dc9f72f5418f1885f4b89a5e664e',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py': 'b7569231226484b0bdd98c40ace14a82672b2138a0aab77711e559a4d9b8ccbc',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py': 'eedcd633cf10b0797c331662507d276f8140195b37c1ed0b605da996ee205603',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/steward_develop_county_action_contract.py': '3a029fc7016922adb773e7ee8192b8c0a12a95e097f08976c0bd1f70df24be12',
                'ck3_autonomous_player/src/xar_autoplayer/bridge/steward_develop_county_contract.py': '663e149d549c2f7a830284c9e8522ec2fc72c2c1be79e5bb7185161e60b3188d',
                'ck3_autonomous_player/native_bridge/src/steward_develop_county_action_v1.cpp': '31f8ac3e392ebd9da78c9a7f413c915a55d58d81f263de18b98f7879badf6453',
                'ck3_autonomous_player/native_bridge/research/steward_develop_county_action_v1_abi.json': 'c64dee3e0b7a5f1c3855ace909374156e378b2587d941bea1b1efb010b36574c',
                'ck3_autonomous_player/tests/unit/test_steward_develop_county_action_v1_bridge.py': '8d9e5545ae498e834cf8032dfba07adc564ef09b5d617757041b96e610c9326c',
                'ck3_autonomous_player/tests/fixtures/steward_develop_county_12003_material/develop_material_available.json': 'e16db0f94a0e55084a2e658905066d7d54f3c345f1a5548713cc2d471506c586',
            }
            def pins():
                return {name: hashlib.sha256((repo / name).read_bytes()).hexdigest() for name in paths}
            if pins() != paths:
                raise RuntimeError('actual steward producer/consumer source drift')
            sys.path.insert(0, str(repo / 'ck3_autonomous_player/src'))
            from xar_autoplayer.bridge import native_driver
            from xar_autoplayer.bridge import steward_develop_county_action_contract as original
            if hasattr(native_driver.NativeHeadlessGameplayDriver, 'change_steward_develop_county_task_v1'):
                raise RuntimeError('headless action qualification changed; requalify the real producer')
            source = repo / 'ck3_autonomous_player/src/xar_autoplayer/bridge/steward_develop_county_action_contract.py'
            for producer in (original.build_change_steward_develop_county_request_v1,
                             original.normalize_change_steward_develop_county_ack_v1,
                             original.normalize_change_steward_develop_county_receipt_v1):
                if Path(producer.__code__.co_filename).resolve() != source.resolve():
                    raise RuntimeError('oracle did not retain the actual producer')
            test_path = repo / 'ck3_autonomous_player/tests/unit/test_steward_develop_county_action_v1_bridge.py'
            spec = importlib.util.spec_from_file_location('original_steward_compatibility', test_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            service_source = (repo / 'ck3_autonomous_player/src/xar_autoplayer/bridge/service.py').resolve()
            for producer in (module.GameplayBridgeService.change_steward_develop_county_task_v1,
                             module.GameplayBridgeService.query_steward_develop_county_candidates_v1):
                if Path(producer.__code__.co_filename).resolve() != service_source:
                    raise RuntimeError('same-config oracle substituted the actual service/query producer')
            if Path(module._ck3_change_steward_develop_county_task_v1.__code__.co_filename).resolve() != (repo / 'ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_server.py').resolve():
                raise RuntimeError('same-config oracle substituted the actual MCP argument adapter')
            with contextlib.redirect_stdout(sys.stderr):
                result = unittest.TextTestRunner(stream=sys.stderr).run(unittest.defaultTestLoader.loadTestsFromModule(module))
            if not result.wasSuccessful() or result.skipped or result.testsRun < 6:
                raise RuntimeError('whole original producer/service/MCP module failed, skipped or was incomplete')
            # Composition deliberately exposes the actual current headless method
            # surface: query transport exists, typed action executor is absent.
            # All service/query/MCP functions remain the pinned actual originals.
            material_path = repo / 'ck3_autonomous_player/tests/fixtures/steward_develop_county_12003_material/develop_material_available.json'
            material = json.loads(material_path.read_text(encoding='utf-8'))['result']['steward_develop_county_candidates']
            class CurrentHeadlessConfiguration:
                def __init__(self, case):
                    self.case = case
                    self.query_calls = 0
                    self.candidate = copy.deepcopy(material if case == 'material' else module._candidate_frame())
                    self.snapshot = module._ActionDriver().take_snapshot()
                    if case == 'material':
                        self.snapshot.update(native_revision=self.candidate['snapshot_revision'], date_raw=self.candidate['observed_date_raw'])
                    if case == 'paused_and_stale':
                        self.snapshot['paused'] = False
                    self.caps = module._ActionDriver().capabilities()
                    if case == 'transport_missing':
                        self.caps['bridge_capabilities'].remove(original.CHANGE_STEWARD_DEVELOP_COUNTY_TASK_V1_TRANSPORT_CAPABILITY)
                    if case == 'query_missing':
                        self.caps['bridge_capabilities'].remove(module.QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_CAPABILITY)
                def capabilities(self):
                    return copy.deepcopy(self.caps)
                def take_snapshot(self):
                    return copy.deepcopy(self.snapshot)
                def execute_step(self, step, *, expected_revision=None):
                    if step != module.QUERY_STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_STEP or expected_revision != module.PUBLIC_REVISION:
                        raise AssertionError('same-config oracle attempted an unexpected operation')
                    self.query_calls += 1
                    return {'step': step, 'accepted': True, 'status': 'available', 'query_sequence': 1,
                            'snapshot_revision': self.snapshot['native_revision'],
                            'steward_develop_county_candidates': copy.deepcopy(self.candidate), 'backend_id': 'native-headless',
                            'steward_develop_county_candidates_ready': True, 'queried_snapshot_id': self.snapshot['snapshot_id'],
                            'queried_revision': self.snapshot['revision'], 'queried_native_revision': self.snapshot['native_revision']}
            service_rows = []
            for name in ('paused_and_stale', 'stale', 'query_missing', 'wrong_steward', 'wrong_county',
                         'transport_missing', 'executor_missing', 'material'):
                driver = CurrentHeadlessConfiguration(name)
                if hasattr(driver, 'change_steward_develop_county_task_v1'):
                    raise RuntimeError('same-config driver unexpectedly gained an action executor')
                expected_revision = 8 if name in ('paused_and_stale', 'stale') else module.PUBLIC_REVISION
                steward = module.STEWARD + (1 if name == 'wrong_steward' else 0)
                county = module.COUNTY + (1 if name == 'wrong_county' else 0)
                if name == 'material':
                    steward = driver.candidate['steward_character_id']
                    county = driver.candidate['candidates'][0]['county_title_id']
                try:
                    module._ck3_change_steward_develop_county_task_v1(module.GameplayBridgeService(driver),
                            steward, county, expected_revision, True)
                except Exception as failure:
                    error = {'python_error': type(failure).__name__, 'message': str(failure)}
                else:
                    raise RuntimeError('actual no-executor original service unexpectedly returned an ACK')
                service_rows.append(dict(case=name, councillor=steward, county=county, expected_revision=expected_revision,
                        snapshot=driver.snapshot, candidate=driver.candidate, capabilities=driver.caps,
                        query_calls=driver.query_calls, **error))
            request = module._request()
            ack = {True: original.normalize_change_steward_develop_county_ack_v1(module._ack(request, submitted=True), expected_request=request),
                   False: original.normalize_change_steward_develop_county_ack_v1(module._ack(request, submitted=False), expected_request=request)}
            cases = json.load(sys.stdin)['cases']
            rows = []
            for case in cases:
                value = json.loads(case['input_json'])
                try:
                    normalized = (original.normalize_change_steward_develop_county_ack_v1(value, expected_request=request)
                                  if case['kind'] == 'ack' else
                                  original.normalize_change_steward_develop_county_receipt_v1(value, expected_ack=ack[case['submitted']]))
                except (ValueError, TypeError):
                    rows.append({'case_id': case['case_id'], 'status': 'rejected'})
                else:
                    rows.append({'case_id': case['case_id'], 'status': 'accepted', 'value': normalized})
            if pins() != paths:
                raise RuntimeError('actual original sources changed during compatibility regression')
            json.dump({'original_tests': result.testsRun, 'skipped': len(result.skipped),
                       'request': dataclasses.asdict(request), 'results': rows, 'service_rows': service_rows}, sys.stdout,
                      ensure_ascii=False, allow_nan=False, separators=(',', ':'))
            """;

    private record Case(String kind, ObjectNode value, boolean submitted, boolean strictTokenDifference) { }

    @Test void wholeActualOriginalModuleAndProducerDifferentialRetainTheUnsupportedBoundary() throws Exception {
        Path python = Path.of(required("xar.python")).toRealPath();
        Path repository = Path.of(required("xar.repository.root")).toRealPath();
        List<Case> cases = new ArrayList<>();
        cases.add(new Case("ack", DevelopmentStewardActionTest.ack(true), true, false));
        cases.add(new Case("ack", DevelopmentStewardActionTest.ack(false), false, false));
        cases.add(new Case("ack", DevelopmentStewardActionTest.ack(true).put("request_id", "other-request"), true, false));
        // Original Python uses equality for these echoed fields. Java follows
        // the explicit integer-token requirement instead of accepting aliases.
        cases.add(new Case("ack", DevelopmentStewardActionTest.ack(true).put("schema_version", true), true, true));
        cases.add(new Case("ack", DevelopmentStewardActionTest.ack(true).put("councillor_character_id", 32910.0), true, true));
        cases.add(new Case("receipt", DevelopmentStewardActionTest.receipt(true, false), true, false));
        cases.add(new Case("receipt", DevelopmentStewardActionTest.receipt(false, true), false, false));
        cases.add(new Case("receipt", DevelopmentStewardActionTest.receipt(false, false), true, false));
        cases.add(new Case("receipt", DevelopmentStewardActionTest.receipt(true, false).put("post_snapshot_revision", 7), true, false));
        cases.add(new Case("receipt", DevelopmentStewardActionTest.receipt(true, false).put("progress_current_raw", Long.MIN_VALUE)
                .put("progress_max_raw", Long.MAX_VALUE), true, false));
        cases.add(new Case("receipt", DevelopmentStewardActionTest.receipt(true, false).put("progress_frozen", 0), true, false));
        cases.add(new Case("receipt", DevelopmentStewardActionTest.receipt(true, false).put("schema_version", true), true, true));
        ObjectMapper mapper = new ObjectMapper();
        ObjectNode request = StrictJson.object();
        ArrayNode values = request.putArray("cases");
        for (int index = 0; index < cases.size(); index++) {
            Case vector = cases.get(index);
            values.addObject().put("case_id", index).put("kind", vector.kind()).put("submitted", vector.submitted())
                    .put("input_json", mapper.writeValueAsString(vector.value()));
        }
        ProcessBuilder builder = new ProcessBuilder(python.toString(), "-I", "-B", "-X", "utf8", "-c", SCRIPT,
                repository.toString()).directory(repository.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        Process process = builder.start();
        byte[] output;
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            var stdout = executor.submit(() -> bounded(process.getInputStream(), 262144));
            var stderr = executor.submit(() -> bounded(process.getErrorStream(), 262144));
            try {
                try (var input = process.getOutputStream()) { input.write(StrictJson.canonical(request)); }
                if (!process.waitFor(60, TimeUnit.SECONDS)) throw new IOException("actual original steward whole module timed out");
                output = stdout.get(10, TimeUnit.SECONDS);
                assertEquals(0, process.exitValue(), new String(stderr.get(10, TimeUnit.SECONDS), StandardCharsets.UTF_8));
            } finally {
                if (process.isAlive()) {
                    process.destroyForcibly();
                    if (!process.waitFor(10, TimeUnit.SECONDS)) throw new IOException("original steward child did not terminate");
                }
            }
        }
        JsonNode original = StrictJson.parse(output, 262144);
        assertTrue(original.get("original_tests").intValue() >= 6); assertEquals(0, original.get("skipped").intValue());
        assertEquals(8, original.get("service_rows").size());
        for (JsonNode row : original.get("service_rows")) {
            var fault = DevelopmentStewardServiceTest.evaluateOriginalConfiguration(row);
            assertEquals(row.get("python_error").textValue(), fault.kind().pythonName(), row.get("case").textValue());
            assertEquals(row.get("message").textValue(), fault.message(), row.get("case").textValue());
            assertEquals(fault, DevelopmentStewardService.decodeFault(DevelopmentStewardService.encodeFault(fault)));
            boolean beforeRead = fault.error() == DevelopmentStewardService.Error.PAUSED_REQUIRED
                    || fault.error() == DevelopmentStewardService.Error.STALE_REVISION
                    || fault.error() == DevelopmentStewardService.Error.QUERY_UNSUPPORTED;
            assertEquals(beforeRead ? 0 : 1, row.get("query_calls").intValue(), row.get("case").textValue());
            assertEquals(beforeRead, fault.candidateOriginal().isEmpty());
            if (row.get("case").textValue().equals("executor_missing")) {
                var action = new DevelopmentStewardAction.Request("steward-oracle-1", row.get("councillor").intValue(),
                        row.get("county").intValue(), row.get("expected_revision").bigIntegerValue(), true);
                var fixture = DevelopmentStewardServiceTest.fixture(action, row.get("candidate"), row.get("snapshot"), row.get("capabilities"));
                var capabilities = DevelopmentStewardService.bindCapabilities(fixture.facts(), fixture.hello(), fixture.hello(), fixture.hello());
                byte[] changedCached = fixture.hello().clone(); changedCached[changedCached.length - 1] ^= 1;
                assertThrows(IllegalArgumentException.class,
                        () -> DevelopmentStewardService.bindCapabilities(fixture.facts(), changedCached, fixture.hello(), fixture.hello()));
                byte[] changedArchive = fixture.hello().clone(); changedArchive[changedArchive.length - 1] ^= 1;
                assertThrows(IllegalArgumentException.class,
                        () -> DevelopmentStewardService.bindCapabilities(fixture.facts(), fixture.hello(), changedArchive, fixture.hello()));
                var otherRead = DevelopmentStewardServiceTest.fixture(action, row.get("candidate"), row.get("snapshot"), row.get("capabilities"));
                assertThrows(IllegalArgumentException.class,
                        () -> DevelopmentStewardService.currentHeadlessRejection(otherRead.facts(), capabilities,
                                DevelopmentStewardSameFrameTest.sources()));
            }
        }
        assertArrayEquals(StrictJson.canonical(original.get("request")), DevelopmentStewardAction.encodeRequest(DevelopmentStewardActionTest.request()).bytes());
        assertEquals(cases.size(), original.get("results").size());
        for (int index = 0; index < cases.size(); index++) {
            Case vector = cases.get(index); JsonNode expected = original.get("results").get(index);
            RawJson raw = new RawJson(mapper.writeValueAsBytes(vector.value()));
            assertEquals(index, expected.get("case_id").intValue());
            if (vector.strictTokenDifference() || expected.get("status").textValue().equals("rejected")) {
                if (vector.strictTokenDifference()) assertEquals("accepted", expected.get("status").textValue());
                assertThrows(IllegalArgumentException.class, () -> decode(vector, raw));
            } else {
                assertEquals("accepted", expected.get("status").textValue());
                assertArrayEquals(StrictJson.canonical(expected.get("value")), decode(vector, raw).bytes());
            }
        }
    }

    private static RawJson decode(Case vector, RawJson raw) {
        var request = DevelopmentStewardActionTest.request();
        if (vector.kind().equals("ack")) return DevelopmentStewardAction.encodeAck(DevelopmentStewardAction.decodeAck(raw, request));
        var ack = DevelopmentStewardAction.decodeAck(DevelopmentStewardActionTest.raw(DevelopmentStewardActionTest.ack(vector.submitted())), request);
        return DevelopmentStewardAction.encodeReceipt(DevelopmentStewardAction.decodeReceipt(raw, ack));
    }
    private static String required(String property) {
        String value = System.getProperty(property);
        if (value == null || value.isBlank()) throw new IllegalStateException(property + " required; original producer NOT_RUN, no skip");
        return value;
    }
    private static byte[] bounded(InputStream input, int maximum) throws IOException {
        try (input; var output = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[4096]; int count;
            while ((count = input.read(buffer)) != -1) {
                if (output.size() + count > maximum) throw new IOException("original producer output limit");
                output.write(buffer, 0, count);
            }
            return output.toByteArray();
        }
    }
}
