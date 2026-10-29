package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesData.*;
import static org.xar.ck3.control.nativebridge.capabilities.frontend_rules.FrontendRulesPostconditions.*;

/** Executes the original pure producer and actual original driver methods, not a rewritten Python model. */
final class FrontendRulesProducerDifferentialTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final Source SOURCE = new Source(new Binding(123, BigInteger.ONE), Build.CK3_12003);
    private static final String PRODUCER = """
        import json, pathlib, runpy, sys
        root = pathlib.Path(sys.argv[1]).resolve()
        sys.path.insert(0, str(root / 'ck3_autonomous_player' / 'src'))
        unit = root / 'ck3_autonomous_player' / 'tests' / 'unit'
        rules = runpy.run_path(str(unit / 'test_frontend_game_rules_control_contract.py'))
        h = rules['driver_harness']()
        before = rules['values']()
        selected = h.select_frontend_game_rule_v1('zg361_enabled', 'zg361_on', 'zg361_off')
        selection_calls = h.calls[:]
        closed = h.apply_and_hide_frontend_game_rules_v1()
        h_bad = rules['driver_harness'](); h_bad.change_other = True
        rejected_other = False
        try: h_bad.select_frontend_game_rule_v1('zg361_enabled', 'zg361_on', 'zg361_off')
        except RuntimeError: rejected_other = True
        h_stale = rules['driver_harness']()
        rejected_stale = False
        try: h_stale.select_frontend_game_rule_v1('zg361_enabled', 'zg361_off', 'zg361_on')
        except ValueError: rejected_stale = True
        print(json.dumps({'before': before, 'window': rules['window'](), 'selected': selected,
            'selection_calls': selection_calls, 'closed': closed, 'all_calls': h.calls,
            'other_rejected': rejected_other, 'other_mutations': sum(c[0] == 'select-frontend-game-rule-v1' for c in h_bad.calls),
            'stale_rejected': rejected_stale, 'stale_mutations': sum(c[0] == 'select-frontend-game-rule-v1' for c in h_stale.calls)}, separators=(',', ':')))
        """;

    private static ObjectNode originalProducer() throws Exception {
        String configured = System.getProperty("xar.repository.root");
        assertNotNull(configured, "actual legacy workspace must be supplied; this regression cannot pass by skipping its original producer");
        assertFalse(configured.isBlank(), "xar.repository.root is mandatory");
        Path root = Path.of(configured).toAbsolutePath().normalize();
        assertTrue(Files.isRegularFile(root.resolve("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py")), "original producer unavailable");
        String python = System.getProperty("xar.python"); assertNotNull(python, "xar.python is mandatory"); assertFalse(python.isBlank(), "xar.python is mandatory");
        Process child = new ProcessBuilder(python, "-X", "utf8", "-c", PRODUCER, root.toString()).redirectErrorStream(true).start();
        try (var readers = Executors.newVirtualThreadPerTaskExecutor()) {
            var captured = readers.submit(() -> {
                try (var stdout = child.getInputStream()) {
                    byte[] bytes = stdout.readNBytes(1024 * 1024 + 1);
                    if (bytes.length > 1024 * 1024) throw new IOException("original pure producer output exceeded explicit bound");
                    return bytes;
                }
            });
            try {
                assertTrue(child.waitFor(30, TimeUnit.SECONDS),
                        () -> "original pure producer timed out; stdout read completed=" + captured.isDone());
                byte[] output = captured.get(5, TimeUnit.SECONDS);
                assertEquals(0, child.exitValue(), () -> "original pure producer failed: " + new String(output, StandardCharsets.UTF_8));
                return FrontendRulesCodec.object(new RawJson(output));
            } finally {
                if (child.isAlive()) child.destroyForcibly();
            }
        }
    }
    private static RawJson raw(JsonNode value) { try { return new RawJson(JSON.writeValueAsBytes(value)); } catch (IOException error) { throw new IllegalArgumentException(error); } }
    @Test void actualProducerSelectionAndClosureAgreeWithTypedReducersAndWireRequest() throws Exception {
        ObjectNode original = originalProducer(); JsonNode selected = original.get("selected"), closed = original.get("closed");
        RuleSelections before = FrontendRulesCodec.selections(raw(original.get("before")), SOURCE, BigInteger.ONE, false);
        RuleWindow window = FrontendRulesCodec.window(raw(original.get("window")), SOURCE, BigInteger.TWO);
        var request = new FrontendRulesRequests.SelectRule(new ScriptKey("zg361_enabled"), new ScriptKey("zg361_on"), new ScriptKey("zg361_off"));
        RulesAck acknowledgement = FrontendRulesCodec.rulesAck(raw(selected.get("acknowledgement")), SOURCE, RulesAction.SELECT);
        RuleSelections after = FrontendRulesCodec.selections(raw(selected.get("observation")), SOURCE, BigInteger.valueOf(4), false);
        SelectionProof proof = selected(before, window, request, acknowledgement, BigInteger.valueOf(3), after);
        assertFalse(proof.appliedSettingsProven());
        assertEquals(request.desiredSettingKey(), proof.observation().selected(request.ruleKey()).orElseThrow());
        JsonNode fields = FrontendRulesCodec.object(request.nativeRequest().additionalFields());
        assertEquals("zg361_enabled", fields.get("rule_key").textValue());
        assertEquals("zg361_on", fields.get("expected_current_setting_key").textValue());
        assertEquals("zg361_off", fields.get("desired_setting_key").textValue());
        assertEquals(3, fields.size());
        for (JsonNode call : original.get("selection_calls")) {
            assertEquals(0, call.get(1).get("expected_revision").intValue());
            assertTrue(call.get(1).get("allow_frontend_revision_zero").booleanValue());
        }
        RulesAck closeAck = FrontendRulesCodec.rulesAck(raw(closed.get("acknowledgement")), SOURCE, RulesAction.APPLY_AND_HIDE);
        RuleWindow closeWindow = FrontendRulesCodec.window(raw(closed.get("window_observation")), SOURCE, BigInteger.valueOf(9));
        ClosureProof closeProof = closed(after, closeAck, BigInteger.valueOf(8), closeWindow);
        assertTrue(closeProof.windowClosedProven()); assertFalse(closeProof.appliedSettingsProven());
        assertTrue(original.get("other_rejected").booleanValue()); assertEquals(1, original.get("other_mutations").intValue());
        assertTrue(original.get("stale_rejected").booleanValue()); assertEquals(0, original.get("stale_mutations").intValue());
    }
    @Test void originalShapesRejectWrongTypesMissingFieldsAndFalseClosure() throws Exception {
        ObjectNode original = originalProducer(); ObjectNode window = (ObjectNode) original.get("window");
        for (String key : List.of("schema_version", "window_visible", "may_edit", "window_closed_proven")) {
            ObjectNode malformed = window.deepCopy(); malformed.put(key, 1.0);
            assertThrows(IllegalArgumentException.class, () -> FrontendRulesCodec.window(raw(malformed), SOURCE, BigInteger.ONE), key);
            ObjectNode missing = window.deepCopy(); missing.remove(key);
            assertThrows(IllegalArgumentException.class, () -> FrontendRulesCodec.window(raw(missing), SOURCE, BigInteger.ONE), key);
        }
        ObjectNode boolCount = (ObjectNode) original.get("before").deepCopy(); boolCount.put("selection_count", true);
        assertThrows(IllegalArgumentException.class, () -> FrontendRulesCodec.selections(raw(boolCount), SOURCE, BigInteger.ONE, false));
        ObjectNode wrongField = (ObjectNode) original.get("before").deepCopy(); ((ObjectNode) wrongField.get("selections").get(0)).put("unmigrated_alias", "on");
        assertThrows(IllegalArgumentException.class, () -> FrontendRulesCodec.selections(raw(wrongField), SOURCE, BigInteger.ONE, false));
        RuleSelections before = FrontendRulesCodec.selections(raw(original.get("before")), SOURCE, BigInteger.ONE, false);
        RulesAck ack = FrontendRulesCodec.rulesAck(raw(original.get("closed").get("acknowledgement")), SOURCE, RulesAction.APPLY_AND_HIDE);
        RuleWindow open = FrontendRulesCodec.window(raw(window), SOURCE, BigInteger.TEN);
        assertThrows(IllegalArgumentException.class, () -> closed(before, ack, BigInteger.valueOf(9), open));
    }
    @Test void rawBoundaryPreservesLargeIdentitiesAndRejectsDuplicatesOrBooleanIntegers() {
        assertThrows(IllegalArgumentException.class, () -> new RawJson("{\"ready\":true,\"ready\":false}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> FrontendRulesCodec.integer(FrontendRulesCodec.object(new RawJson("{\"id\":true}".getBytes(StandardCharsets.UTF_8))), "id", BigInteger.ZERO, U64_MAX));
        BigInteger value = new BigInteger("18446744073709551615");
        RawJson raw = new RawJson(("{\"id\":" + value + "}").getBytes(StandardCharsets.UTF_8));
        assertEquals(value, FrontendRulesCodec.integer(FrontendRulesCodec.object(raw), "id", BigInteger.ONE, U64_MAX));
        assertArrayEquals(raw.bytes(), new RawJson(raw.bytes()).bytes());
    }
}
