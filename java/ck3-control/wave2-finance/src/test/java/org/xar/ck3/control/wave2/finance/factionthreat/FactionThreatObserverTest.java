package org.xar.ck3.control.wave2.finance.factionthreat;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.xar.ck3.control.wave2.finance.factionthreat.FactionThreatObserver.*;

final class FactionThreatObserverTest {
    private static final ObjectMapper JSON = new ObjectMapper();

    @TestFactory
    List<DynamicTest> unchangedProducerGoldenAndActualAdapterPort() throws IOException {
        JsonNode root = golden();
        assertEquals("xar.ck3.java.faction-threat-producer-golden/v1", root.path("schema").textValue());
        assertEquals(0, root.path("capture").path("native_rpc_count").intValue());
        assertTrue(root.path("cases").size() >= 35, "the retained whole golden is mandatory");
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode vector : root.path("cases")) {
            tests.add(DynamicTest.dynamicTest(vector.path("name").textValue(), () -> {
                byte[] requestBytes = JSON.writeValueAsBytes(vector.path("input"));
                Request request = FactionThreatCodec.decodeRequest(requestBytes);
                FixtureDriver driver = new FixtureDriver(vector.path("driver"));
                Response response = FactionThreatObserver.observe(request, new ExistingFactionAlertAdapter(driver));
                JsonNode actual = JSON.readTree(FactionThreatCodec.encode(response));
                assertEquals(vector.path("expected"), actual);
                assertEquals(vector.path("expected_observer_calls"), JSON.readTree(JSON.writeValueAsBytes(driver.calls)));
                Request restored = FactionThreatCodec.decodeRequest(JSON.writeValueAsBytes(JSON.readTree(requestBytes)));
                FixtureDriver repeated = new FixtureDriver(vector.path("driver"));
                assertEquals(actual, JSON.readTree(FactionThreatCodec.encode(FactionThreatObserver.observe(
                        restored, new ExistingFactionAlertAdapter(repeated)))));
                if (response instanceof Observed observed) {
                    byte[] copy = observed.nativeRow().originalJson();
                    copy[0] = 0;
                    assertEquals(actual.path("native_row"), JSON.readTree(observed.nativeRow().originalJson()));
                    assertFalse(actual.path("exact_ultimatum_timing_ready").booleanValue());
                    assertEquals("not_inferred", actual.path("faction_departure_or_threat_resolution").textValue());
                }
            }));
        }
        return List.copyOf(tests);
    }

    @Test
    void rawFloatAndBooleanIdentityTokensAreRejectedWithoutJsonTreeNormalization() throws IOException {
        String request = JSON.writeValueAsString(baseInput());
        assertTrue(request.contains("\"expected_revision\":507"));
        assertThrows(IllegalArgumentException.class, () -> decode(request.replace("\"expected_revision\":507", "\"expected_revision\":507.0")));
        assertThrows(IllegalArgumentException.class, () -> decode(request.replace("\"expected_revision\":507", "\"expected_revision\":true")));
        assertThrows(IllegalArgumentException.class, () -> decode(request.replace("\"snapshot_revision\":506", "\"snapshot_revision\":506.0")));
        assertThrows(IllegalArgumentException.class, () -> decode(request.replace("\"source_faction_id\":54", "\"source_faction_id\":true")));
        assertThrows(IllegalArgumentException.class, () -> decode(request.replace("\"dangerous_by_stock_rule\":false", "\"dangerous_by_stock_rule\":0")));
    }

    @Test
    void envelopeFieldsAndMalformedUtf8AreRejectedWhileSdkExtensionsRemainProjected() throws IOException {
        ObjectNode request = baseInput();
        request.put("unexpected", true);
        assertThrows(IllegalArgumentException.class, () -> FactionThreatCodec.decodeRequest(JSON.writeValueAsBytes(request)));
        request.remove("unexpected");
        request.remove("expected_revision");
        assertThrows(IllegalArgumentException.class, () -> FactionThreatCodec.decodeRequest(JSON.writeValueAsBytes(request)));
        assertThrows(IllegalArgumentException.class, () -> decode("{} {}"));
        assertThrows(IllegalArgumentException.class, () -> decode("{\"snapshot\":{},\"snapshot\":{}}"));
        assertThrows(IllegalArgumentException.class, () -> FactionThreatCodec.decodeRequest(new byte[]{'{', '"', (byte) 0xC3, '"', ':', '0', '}'}));
        assertThrows(IllegalArgumentException.class, () -> FactionThreatCodec.decodeRequest(new byte[FactionThreatCodec.MAX_BYTES + 1]));
        assertInstanceOf(SelectedGiftRequest.class, FactionThreatCodec.decodeRequest(JSON.writeValueAsBytes(baseInput())));
    }

    @Test
    void nullMemberVectorDoesNotBecomeKnownEmptyAndMissingFrameDoesNotQualify() throws IOException {
        ObjectNode request = baseInput();
        ObjectNode alert = (ObjectNode) request.path("history").get(0).path("result").path("player_faction_alerts");
        ObjectNode row = (ObjectNode) alert.path("targeting_factions").get(0);
        row.putNull("character_member_ids");
        assertThrows(IllegalArgumentException.class, () -> FactionThreatCodec.decodeRequest(JSON.writeValueAsBytes(request)));
        ObjectNode empty = JSON.createObjectNode();
        empty.putObject("player_faction_alerts").put("status", "available");
        Alert projected = FactionThreatCodec.decodeExistingObserverResult(JSON.writeValueAsBytes(empty));
        assertTrue(projected.frame().isEmpty());
        assertFalse(projected.readiness().complete());
    }

    @Test
    void unexpectedDriverFailurePropagatesInsteadOfBecomingUnavailable() throws IOException {
        ObjectNode request = baseInput();
        request.set("history", JSON.createArrayNode());
        Request input = FactionThreatCodec.decodeRequest(JSON.writeValueAsBytes(request));
        ExistingAlertReader failed = new ExistingAlertReader() {
            @Override public boolean supportsExistingObserver() { return true; }
            @Override public ReadResult readExistingObserver(BigInteger expectedRevision) {
                throw new IllegalStateException("actual unrelated driver failure");
            }
        };
        assertThrows(IllegalStateException.class, () -> FactionThreatObserver.observe(input, failed));
    }

    @Test
    void typedModelCannotAssertDangerIndependentOfNativeRow() throws IOException {
        Request input = FactionThreatCodec.decodeRequest(JSON.writeValueAsBytes(baseInput()));
        Response response = FactionThreatObserver.observe(input, new FixtureDriverReader());
        Observed observed = assertInstanceOf(Observed.class, response);
        assertFalse(observed.dangerousResponseReady());
        assertThrows(IllegalArgumentException.class, () -> new Observed(observed.origin(), observed.gift(),
                observed.frame(), true, observed.nativeRow()));
    }

    @Test
    void observedRowOpaqueDecimalsSurviveHistoryProjectionAndResponseWithoutDoubleRounding() throws IOException {
        ObjectNode input = baseInput();
        ObjectNode row = (ObjectNode) input.path("history").get(0).path("result")
                .path("player_faction_alerts").path("targeting_factions").get(0);
        row.putNull("decimal_extension");
        String request = JSON.writeValueAsString(input).replace("\"decimal_extension\":null",
                "\"decimal_extension\":{\"zero\":0e0,\"fraction\":0.12345678901234567890123456789,\"huge\":1e400}");
        Response response = FactionThreatObserver.observe(decode(request), new FixtureDriverReader());
        ObjectMapper exact = new ObjectMapper().enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS);
        JsonNode extension = exact.readTree(FactionThreatCodec.encode(response)).path("native_row").path("decimal_extension");
        assertTrue(extension.path("zero").isFloatingPointNumber());
        assertTrue(extension.path("huge").isFloatingPointNumber());
        assertEquals(0, new BigDecimal("0.12345678901234567890123456789").compareTo(extension.path("fraction").decimalValue()));
        assertEquals(0, new BigDecimal("1e400").compareTo(extension.path("huge").decimalValue()));
    }

    private static final class FixtureDriverReader implements ExistingAlertReader {
        @Override public boolean supportsExistingObserver() { throw new AssertionError("history must be reused"); }
        @Override public ReadResult readExistingObserver(BigInteger revision) { throw new AssertionError("history must be reused"); }
    }

    private record Call(String step, BigInteger expected_revision) { }

    private static final class FixtureDriver implements ExistingFactionAlertAdapter.ExistingDriverPort {
        private final JsonNode specification;
        private final List<Call> calls = new ArrayList<>();
        FixtureDriver(JsonNode specification) { this.specification = specification; }
        @Override public List<String> existingBridgeCapabilities() {
            return specification.path("supports").booleanValue() ? List.of(CAPABILITY) : List.of();
        }
        @Override public ExistingFactionAlertAdapter.Invocation queryPlayerFactionAlerts(BigInteger expectedRevision) {
            calls.add(new Call(STEP, expectedRevision));
            if (specification.has("error")) {
                return new ExistingFactionAlertAdapter.ObserverUnavailable(
                        specification.path("error").textValue().equals("bridge")
                                ? ReadFailureKind.BRIDGE_UNAVAILABLE : ReadFailureKind.UNSUPPORTED_STEP,
                        specification.path("message").textValue());
            }
            try {
                return new ExistingFactionAlertAdapter.ObserverPacket(JSON.writeValueAsBytes(specification.path("result")));
            } catch (IOException failure) { throw new IllegalStateException(failure); }
        }
    }

    private static JsonNode golden() throws IOException {
        try (InputStream input = FactionThreatObserverTest.class.getResourceAsStream("/factionthreat/python-golden-v1.json")) {
            assertNotNull(input, "original producer golden must be captured before Java qualification");
            byte[] bytes = input.readNBytes(110_001);
            assertTrue(bytes.length <= 110_000, "bounded golden");
            return JSON.readTree(bytes);
        }
    }

    private static ObjectNode baseInput() throws IOException {
        return (ObjectNode) golden().path("cases").get(0).path("input").deepCopy();
    }

    private static Request decode(String value) {
        return FactionThreatCodec.decodeRequest(value.getBytes(StandardCharsets.UTF_8));
    }
}
