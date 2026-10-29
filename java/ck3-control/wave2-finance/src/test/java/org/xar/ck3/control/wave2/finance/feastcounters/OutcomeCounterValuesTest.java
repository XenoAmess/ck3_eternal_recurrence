package org.xar.ck3.control.wave2.finance.feastcounters;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.wave2.finance.feastcounters.OutcomeCounterValues.Presence;
import org.xar.ck3.control.wave2.finance.feastcounters.OutcomeCounterValues.Projection;

final class OutcomeCounterValuesTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String PRODUCER_SHA = "656b02666880395c1bc1e0e3de4d9ff9d1a0d30e1393fc69e1d930aef43b8f3f";
    private static final String BASE = "{\"prestige_raw\":-500000,\"stress_points\":48,\"reveler_present\":true,\"reveler_xp_raw\":6500000}";

    @TestFactory
    Stream<DynamicTest> comparesActualProducerRawTokensAndCounterRoundTrips() throws IOException {
        JsonNode root = golden(); assertEquals(25, root.get("producer_cases").size());
        return StreamSupport.stream(root.get("producer_cases").spliterator(), false).map(row ->
                DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
                    byte[] raw = row.get("input_json").textValue().getBytes(StandardCharsets.UTF_8);
                    if (!row.get("accepted").booleanValue()) {
                        assertThrows(IllegalArgumentException.class, () -> OutcomeCounterCodec.decodeCounters(raw));
                    } else {
                        OutcomeCounterValues value = OutcomeCounterCodec.decodeCounters(raw);
                        byte[] encoded = OutcomeCounterCodec.encodeCounters(value);
                        assertEquals(row.get("result"), JSON.readTree(encoded));
                        assertEquals(value, OutcomeCounterCodec.decodeCounters(encoded));
                    }
                }));
    }

    @TestFactory
    Stream<DynamicTest> comparesActualStartSeedAndLifecycleConsumerValueSubtree() throws IOException {
        JsonNode root = golden(); assertEquals(9, root.get("projection_cases").size());
        return StreamSupport.stream(root.get("projection_cases").spliterator(), false).map(row ->
                DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
                    Projection value = OutcomeCounterCodec.decodeProjection(row.get("input_json").textValue().getBytes(StandardCharsets.UTF_8));
                    assertEquals(row.get("expected"), JSON.readTree(OutcomeCounterCodec.encodeProjection(value)));
                    assertEquals(value, OutcomeCounterCodec.decodeProjection(OutcomeCounterCodec.encodeProjectionInput(value)));
                    Optional<OutcomeCounterValues> originalSeed = OutcomeCounterCodec.decodeStoredSeed(JSON.writeValueAsBytes(row.get("actual_start_seed")));
                    assertEquals(value.before(), originalSeed);
                    assertEquals(row.get("normalized_start_seed"), JSON.readTree(OutcomeCounterCodec.encodeStoredSeed(originalSeed)));
                    assertEquals(value.before().isPresent(), row.get("actual_counter_read_pending_after_start").booleanValue(),
                            "nonterminal Start fixture retains source map presence for the original reader");
                }));
    }

    @Test
    void bindsActualProducerCompleteExistingConsumersAndIsolatedFixtureScope() throws IOException {
        JsonNode root = golden();
        assertEquals("xar.feast-counter-producer-consumer-golden/v1", root.get("schema").textValue());
        assertEquals(PRODUCER_SHA, root.get("source_refs").get(0).get("sha256").textValue());
        assertEquals("xenoamess-full-tower-eb9d2c1186", root.get("machine_id").textValue());
        assertEquals(18, root.get("existing_tests").get("run").intValue());
        assertEquals(0, root.get("existing_tests").get("failures").intValue());
        assertEquals(0, root.get("existing_tests").get("errors").intValue());
        assertEquals(0, root.get("existing_tests").get("skipped").intValue());
        assertEquals("isolated_fixture_ledger_only", root.get("fixture_write_scope").get("kind").textValue());
        assertTrue(root.get("fixture_write_scope").get("retained_bytes").longValue() <= 524_288);
        assertTrue(root.get("capture_scope").textValue().contains("actual Start pending copy"));
    }

    @Test
    void deltaArithmeticKeepsTheFullDifferenceBeyondNativeSignedWidths() {
        var minimum = new OutcomeCounterValues(Optional.of(Long.MIN_VALUE), Optional.of(Integer.MIN_VALUE), Presence.ABSENT, Optional.of(Long.MIN_VALUE));
        var maximum = new OutcomeCounterValues(Optional.of(Long.MAX_VALUE), Optional.of(Integer.MAX_VALUE), Presence.PRESENT, Optional.of(Long.MAX_VALUE));
        Projection value = new Projection(minimum, maximum);
        assertEquals(Optional.of(BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE)), value.changes().prestigeRaw());
        assertEquals(Optional.of(new BigInteger("4294967295")), value.changes().stressPoints());
        assertEquals(value.changes().prestigeRaw(), value.changes().revelerXpRaw());
    }

    @Test
    void knownFalsePresenceAndKnownXpRemainIndependentObservedInputs() {
        var before = new OutcomeCounterValues(Optional.of(0L), Optional.of(0), Presence.ABSENT, Optional.of(1L));
        var after = new OutcomeCounterValues(Optional.of(0L), Optional.of(0), Presence.ABSENT, Optional.of(2L));
        Projection value = new Projection(before, after);
        assertEquals(Optional.of(BigInteger.ONE), value.changes().revelerXpRaw());
        assertTrue(value.observed().revelerPresent());
        assertEquals(Optional.of(new OutcomeCounterValues.PresenceTransition(false, false)), value.presenceTransition());
    }

    @Test
    void nullGroupsStayUnknownAndMissingStrictFieldsAreRejected() throws IOException {
        Projection unknown = OutcomeCounterCodec.decodeProjection("{\"before\":null,\"after\":null}".getBytes(StandardCharsets.UTF_8));
        assertTrue(unknown.before().isEmpty());
        assertEquals(OutcomeCounterValues.unknown(), unknown.beforeValues());
        assertTrue(unknown.changes().prestigeRaw().isEmpty()); assertTrue(unknown.presenceTransition().isEmpty());
        assertFalse(unknown.observed().revelerPresent());
        assertThrows(IllegalArgumentException.class, () -> OutcomeCounterCodec.decodeProjection("{\"before\":null}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> decode(BASE.replace(",\"stress_points\":48", "")));
        assertThrows(IllegalArgumentException.class, () -> decode("null"));
        Optional<OutcomeCounterValues> observedUnknown = Optional.of(OutcomeCounterValues.unknown());
        assertTrue(JSON.readTree(OutcomeCounterCodec.encodeStoredSeed(Optional.empty())).isNull());
        assertTrue(JSON.readTree(OutcomeCounterCodec.encodeStoredSeed(observedUnknown)).isObject());
        assertFalse(OutcomeCounterCodec.decodeStoredSeed(OutcomeCounterCodec.encodeStoredSeed(observedUnknown)).isEmpty());
    }

    @Test
    void rejectsOriginalFloatExponentBoolStringTokensAtTheBoundary() {
        for (String token : List.of("48.0", "48e0", "true", "\"48\"")) {
            assertThrows(IllegalArgumentException.class, () -> decode(BASE.replace("\"stress_points\":48", "\"stress_points\":" + token)), token);
        }
        for (String token : List.of("-500000.0", "-5e5", "false", "\"-500000\"")) {
            assertThrows(IllegalArgumentException.class, () -> decode(BASE.replace("\"prestige_raw\":-500000", "\"prestige_raw\":" + token)), token);
        }
    }

    @Test
    void rejectsDuplicateUnknownFieldsMalformedUtf8TrailingAndOversize() {
        assertThrows(IllegalArgumentException.class, () -> decode("{\"prestige_raw\":1," + BASE.substring(1)));
        assertThrows(IllegalArgumentException.class, () -> decode(BASE.substring(0, BASE.length() - 1) + ",\"unknown\":0}"));
        assertThrows(IllegalArgumentException.class, () -> decode(BASE + " {}"));
        assertThrows(IllegalArgumentException.class, () -> OutcomeCounterCodec.decodeCounters(new byte[] {(byte) 0xC3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> OutcomeCounterCodec.decodeCounters(new byte[OutcomeCounterCodec.MAX_BYTES + 1]));
    }

    @Test
    void nativeMissingFieldAndPersistedNullUseSeparateDeclaredBoundaries() throws IOException {
        assertTrue(OutcomeCounterCodec.decodeNativeCounterFieldProjection("{}".getBytes(StandardCharsets.UTF_8)).isEmpty());
        assertThrows(IllegalArgumentException.class, () -> OutcomeCounterCodec.decodeNativeCounterFieldProjection("{\"outcome_values\":null}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> OutcomeCounterCodec.decodeNativeCounterFieldProjection("{\"future_extension\":[]}".getBytes(StandardCharsets.UTF_8)),
                "field-only projection must not be confused with an entire extensible SDK root");
        assertTrue(OutcomeCounterCodec.decodeStoredSeed("null".getBytes(StandardCharsets.UTF_8)).isEmpty());
        Optional<OutcomeCounterValues> knownUnknown = Optional.of(OutcomeCounterValues.unknown());
        JsonNode missing = JSON.readTree(OutcomeCounterCodec.encodeNativeCounterFieldProjection(Optional.empty()));
        JsonNode observed = JSON.readTree(OutcomeCounterCodec.encodeNativeCounterFieldProjection(knownUnknown));
        assertFalse(missing.has("outcome_values")); assertTrue(observed.get("outcome_values").isObject());
        assertEquals(knownUnknown, OutcomeCounterCodec.decodeNativeCounterFieldProjection(OutcomeCounterCodec.encodeNativeCounterFieldProjection(knownUnknown)));
    }

    private static OutcomeCounterValues decode(String raw) { return OutcomeCounterCodec.decodeCounters(raw.getBytes(StandardCharsets.UTF_8)); }
    private static JsonNode golden() throws IOException {
        try (InputStream input = OutcomeCounterValuesTest.class.getResourceAsStream("/feastcounters/counter-producer-consumer-golden-v1.json")) {
            if (input == null) throw new IOException("required actual producer/consumer golden unavailable");
            return JSON.readTree(input.readAllBytes());
        }
    }
}
