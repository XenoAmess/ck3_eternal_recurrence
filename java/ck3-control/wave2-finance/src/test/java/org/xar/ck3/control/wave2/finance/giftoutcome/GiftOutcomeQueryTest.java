package org.xar.ck3.control.wave2.finance.giftoutcome;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.finance.giftoutcome.GiftOutcomeModel.*;

class GiftOutcomeQueryTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String RESOURCE = "/giftoutcome/original-producer-golden.json";

    @Test void unchangedOriginalProducerToOwnedDriverAdapterAllCases() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.ck3.java.gift-outcome-producer-golden/v1", golden.path("schema").textValue());
        assertFalse(golden.path("capture").path("machine_id").textValue().isBlank());
        assertFalse(golden.path("capture").path("observed_at_utc").textValue().isBlank());
        assertEquals(0, golden.path("capture").path("native_rpc_count").intValue());
        assertEquals(0, golden.path("capture").path("ledger_writes").intValue());
        assertTrue(golden.path("sources").size() >= 5);
        assertTrue(golden.path("cases").size() >= 26);
        for (JsonNode vector : golden.path("cases")) {
            String name = vector.path("name").textValue(); ObjectNode specification = materialize(golden, vector);
            byte[] historyBefore = bytes(specification.get("history")); FixtureOwnedDriver driver = new FixtureOwnedDriver(specification);
            ExistingGiftOutcomeAdapter adapter = new ExistingGiftOutcomeAdapter(driver);
            if (!vector.path("failure").isNull()) {
                assertEquals("PreSubmissionRevisionMismatchError", vector.path("failure").path("class").textValue(), name);
                assertThrows(GiftOutcomeQuery.RevisionMismatchException.class,
                        () -> adapter.queryResolvedFactionGiftOutcome(bytes(specification.get("request"))), name);
            } else {
                byte[] actual = adapter.queryResolvedFactionGiftOutcome(bytes(specification.get("request")));
                JsonNode output = StrictJson.parse(actual, GiftOutcomeCodec.MAX_BYTES);
                assertEquals(vector.get("expected"), output, name);
                if (output.path("status").asText().equals("observed")) {
                    assertFalse(output.path("attributed_to_gift").booleanValue(), name);
                    assertFalse(output.path("gift_submit_performed").booleanValue(), name);
                    assertFalse(output.path("pending_resolution_performed").booleanValue(), name);
                    assertEquals(output, StrictJson.parse(driver.recorded.getFirst(), GiftOutcomeCodec.MAX_BYTES), name);
                }
            }
            assertEquals(vector.get("expected_pair_calls"), JSON.valueToTree(driver.pairCalls), name);
            assertEquals(vector.get("expected_alert_calls"), JSON.valueToTree(driver.alertCalls), name);
            assertEquals(vector.path("expected_record_count").intValue(), driver.recorded.size(), name);
            assertEquals(vector.path("expected_snapshot_count").intValue(), driver.snapshots, name);
            assertArrayEquals(historyBefore, bytes(specification.get("history")), name);
            assertFalse(driver.locked, name);
        }
    }
    @Test void rawIntegerTokensRejectBooleansFloatsStringsAndMissingFields() {
        for (String bad : List.of("true", "1.0", "1e0", "\"1\"", "null")) {
            String raw = "{\"request_id\":\"gift-original\",\"expected_revision\":" + bad + "}";
            assertThrows(ContractViolationException.class, () -> GiftOutcomeCodec.request(utf8(raw)), raw);
        }
        for (String raw : List.of("{\"request_id\":\"gift-original\"}",
                "{\"request_id\":\"gift-original\",\"expected_revision\":9,\"extra\":true}",
                "{\"request_id\":\"a\",\"request_id\":\"b\",\"expected_revision\":9}",
                "{\"request_id\":\"a\",\"expected_revision\":9} {}")) {
            assertThrows(ContractViolationException.class, () -> GiftOutcomeCodec.request(utf8(raw)), raw);
        }
        assertThrows(IllegalArgumentException.class, () -> GiftOutcomeCodec.request(utf8("{\"request_id\":\"\",\"expected_revision\":9}")));
    }
    @Test void realRegisteredNativeDriverServiceMcpProducerChainMatchesTheSameJavaAdapter() throws IOException {
        JsonNode chain = golden().path("registered_consumer");
        assertTrue(chain.path("original_registered_test_assertions_completed").booleanValue());
        assertEquals(5, chain.path("route").size());
        ObjectNode spec = (ObjectNode) chain.path("input").deepCopy(); FixtureOwnedDriver driver = new FixtureOwnedDriver(spec);
        JsonNode output = StrictJson.parse(new ExistingGiftOutcomeAdapter(driver).queryResolvedFactionGiftOutcome(bytes(spec.get("request"))), GiftOutcomeCodec.MAX_BYTES);
        assertEquals(chain.get("expected"), output); assertEquals(1, driver.pairCalls.size());
        assertEquals(1, driver.alertCalls.size()); assertEquals(1, driver.recorded.size());
    }
    @Test void everyKnownIntegerAndBooleanProjectionRejectsWrongRawToken() throws IOException {
        JsonNode base = golden().path("base");
        String snapshot = new String(bytes(base.get("snapshot")), StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class, () -> GiftOutcomeCodec.snapshot(utf8(snapshot.replace("\"native_revision\":12", "\"native_revision\":12.0"))));
        assertThrows(ContractViolationException.class, () -> GiftOutcomeCodec.snapshot(utf8(snapshot.replace("\"character_id\":29829", "\"character_id\":true"))));
        String history = new String(bytes(base.get("history")), StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class, () -> GiftOutcomeCodec.history(utf8(history.replace("\"schema_version\":1", "\"schema_version\":1.0"))));
        String pair = new String(bytes(base.get("pair_result")), StandardCharsets.UTF_8);
        assertThrows(ContractViolationException.class, () -> GiftOutcomeCodec.pairResult(utf8(pair.replace("\"failure_flags\":0", "\"failure_flags\":false"))));
        assertThrows(ContractViolationException.class, () -> GiftOutcomeCodec.pairResult(utf8(pair.replace("\"gift_opinion_present\":true", "\"gift_opinion_present\":1"))));
        assertThrows(ContractViolationException.class, () -> GiftOutcomeCodec.pairResult(utf8(pair.replace("\"recipient_opinion_of_player\":10", "\"recipient_opinion_of_player\":10.0"))));
        assertThrows(ContractViolationException.class, () -> GiftOutcomeCodec.alertResult(utf8("{\"player_faction_alerts\":{\"targeting_factions\":[{\"faction_id\":true}]}}")));
    }
    @Test void projectedSdkExtensionsAndUnboundedPythonIntegersRoundTripWithoutBecomingAuthority() throws IOException {
        JsonNode document = golden(); ObjectNode spec = (ObjectNode) document.path("base").deepCopy();
        ObjectNode receipt = (ObjectNode) spec.path("history").get(1).path("result").path("receipt");
        ObjectNode extension = (ObjectNode) StrictJson.parse(utf8("{\"fraction\":1.0,\"null\":null,\"empty\":[],\"big\":18446744073709551615}"));
        extension.set("fraction", new com.fasterxml.jackson.databind.node.DecimalNode(new java.math.BigDecimal("1.0")));
        receipt.set("sdk_extension", extension);
        ((ObjectNode) spec.path("history").get(0).path("result").path("pending_ledger").path("pending"))
                .put("gold_cost_raw", new BigInteger("18446744073709551615"));
        FixtureOwnedDriver driver = new FixtureOwnedDriver(spec);
        JsonNode output = StrictJson.parse(new ExistingGiftOutcomeAdapter(driver).queryResolvedFactionGiftOutcome(bytes(spec.get("request"))), GiftOutcomeCodec.MAX_BYTES);
        assertEquals(new BigInteger("18446744073709551615"), output.path("original").path("gold_cost_raw").bigIntegerValue());
        assertTrue(output.path("original").path("receipt").path("sdk_extension").path("fraction").isFloatingPointNumber());
        assertTrue(output.path("original").path("receipt").path("sdk_extension").path("null").isNull());
        assertTrue(output.path("original").path("receipt").path("sdk_extension").path("empty").isArray());
    }
    @Test void bindingUsesDictionaryContentAndDefensiveCopies() throws IOException {
        ObjectNode first = (ObjectNode) golden().path("base").path("snapshot").deepCopy();
        first.set("active_event", StrictJson.parse(utf8("{\"a\":1,\"b\":2}")));
        ObjectNode second = first.deepCopy(); second.set("active_event", StrictJson.parse(utf8("{\"b\":2,\"a\":1}")));
        Snapshot snapshot = GiftOutcomeCodec.snapshot(bytes(first));
        assertEquals(snapshot.binding(), GiftOutcomeCodec.snapshot(bytes(second)).binding());
        byte[] copy = snapshot.activeEvent().json(); copy[0] = 0;
        assertEquals(snapshot.binding(), GiftOutcomeCodec.snapshot(bytes(second)).binding());
    }
    private static JsonNode golden() throws IOException {
        try (InputStream stream = GiftOutcomeQueryTest.class.getResourceAsStream(RESOURCE)) {
            assertNotNull(stream, "required original producer capture is unavailable; do not count a skip as pass");
            return StrictJson.parse(stream.readAllBytes(), GiftOutcomeCodec.MAX_BYTES);
        }
    }
    private static ObjectNode materialize(JsonNode golden, JsonNode vector) {
        ObjectNode root = (ObjectNode) golden.path("base").deepCopy();
        for (JsonNode operation : vector.path("operations")) {
            String path = operation.path("path").textValue(); int slash = path.lastIndexOf('/');
            JsonNode parent = root.at(path.substring(0, slash)); String key = path.substring(slash + 1);
            if (parent instanceof ObjectNode object) {
                if (operation.path("remove").asBoolean(false)) object.remove(key); else object.set(key, operation.get("value").deepCopy());
            } else if (parent instanceof ArrayNode array) {
                int index = Integer.parseInt(key);
                if (operation.path("remove").asBoolean(false)) array.remove(index); else array.set(index, operation.get("value").deepCopy());
            } else fail("invalid golden patch " + path);
        }
        return root;
    }
    private static byte[] bytes(JsonNode value) {
        try { return JSON.writeValueAsBytes(value); } catch (IOException error) { throw new IllegalStateException(error); }
    }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }

    private static final class FixtureOwnedDriver implements ExistingGiftOutcomeAdapter.OwnedDriverPort {
        private final ObjectNode spec; private final List<JsonNode> pairCalls = new ArrayList<>();
        private final List<JsonNode> alertCalls = new ArrayList<>(); private final List<byte[]> recorded = new ArrayList<>();
        private boolean locked; private int snapshots;
        FixtureOwnedDriver(ObjectNode spec) { this.spec = spec; }
        @Override public byte[] takeInternalSemanticSnapshot() {
            assertFalse(locked); return bytes(spec.get(++snapshots == 1 ? "snapshot" : "after_snapshot"));
        }
        @Override public <T> T underOriginalHistoryLock(Function<Iterable<byte[]>, T> projection) {
            assertFalse(locked); locked = true;
            try {
                List<byte[]> rows = new ArrayList<>(); for (JsonNode row : spec.path("history")) rows.add(bytes(row));
                return projection.apply(List.copyOf(rows));
            } finally { locked = false; }
        }
        @Override public ExistingGiftOutcomeAdapter.Invocation readOriginalIndependentPair(byte[] request) {
            assertFalse(locked); JsonNode payload = StrictJson.parse(request, GiftOutcomeCodec.MAX_BYTES);
            assertEquals(PAIR_STEP, payload.path("step").textValue()); pairCalls.add(payload);
            if (!spec.path("pair_error").isNull()) return new ExistingGiftOutcomeAdapter.Unavailable(ExistingGiftOutcomeAdapter.ReadFailure.BRIDGE_UNAVAILABLE, spec.path("pair_error").textValue());
            return new ExistingGiftOutcomeAdapter.Packet(bytes(spec.get("pair_result")));
        }
        @Override public ExistingGiftOutcomeAdapter.Invocation queryOriginalPlayerFactionAlerts(BigInteger expectedRevision) {
            assertFalse(locked); ObjectNode call = StrictJson.object(); call.put("step", ALERT_STEP); call.put("expected_revision", expectedRevision); alertCalls.add(call);
            if (!spec.path("alert_error").isNull()) return new ExistingGiftOutcomeAdapter.Unavailable(ExistingGiftOutcomeAdapter.ReadFailure.BRIDGE_UNAVAILABLE, spec.path("alert_error").textValue());
            return new ExistingGiftOutcomeAdapter.Packet(bytes(spec.get("alert_result")));
        }
        @Override public void recordOriginalObservedCommand(String step, boolean ok, byte[] result) {
            assertFalse(locked); assertEquals(STEP, step); assertTrue(ok); recorded.add(result.clone());
        }
    }
}
