package org.xar.ck3.control.wave2.finance.feastterminal;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
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
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.StampObserved;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.BooleanObservation;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.Outcome;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.ParsedJournal;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.Request;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.Status;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.UnknownReason;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalOutcome.UnusableJournal;

final class FeastTerminalPolicyTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String PRODUCER_SHA = "b24bdd23bcbf0139605a7ce98f849ca850b471e33d2d661e9fa9709aef3fa692";

    @TestFactory
    Stream<DynamicTest> comparesActualTerminalProducerAndCanonicalProjectionRoundTrips() throws IOException {
        JsonNode golden = golden();
        assertEquals(48, golden.get("cases").size());
        return StreamSupport.stream(golden.get("cases").spliterator(), false).map(row ->
                DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
                    byte[] raw = row.get("input_json").textValue().getBytes(StandardCharsets.UTF_8);
                    if (!row.get("accepted").booleanValue()) {
                        assertThrows(IllegalArgumentException.class, () -> FeastTerminalCodec.decodeRequest(raw));
                        return;
                    }
                    Request request = FeastTerminalCodec.decodeRequest(raw);
                    Outcome outcome = FeastTerminalPolicy.observe(request);
                    assertEquals(row.get("result"), JSON.readTree(FeastTerminalCodec.encodeOutcome(outcome)));
                    assertEquals(request, FeastTerminalCodec.decodeRequest(FeastTerminalCodec.encodeRequest(request)));
                }));
    }

    @Test
    void goldenBindsOriginalSourceArchivedWireAndExistingWholeModules() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.feast-terminal-producer-golden/v1", golden.get("schema").textValue());
        assertEquals(PRODUCER_SHA, golden.get("source_refs").get(0).get("sha256").textValue());
        assertEquals("xenoamess-full-tower-eb9d2c1186", golden.get("machine_id").textValue());
        assertEquals(6, golden.get("existing_tests").get("run").intValue());
        assertEquals(0, golden.get("existing_tests").get("failures").intValue());
        assertEquals(0, golden.get("existing_tests").get("errors").intValue());
        assertEquals(0, golden.get("existing_tests").get("skipped").intValue());
        assertEquals(3, StreamSupport.stream(golden.get("cases").spliterator(), false)
                .filter(row -> row.get("origin").textValue().equals("archived_native_wire_via_existing_readonly_fixture_driver")).count());
    }

    @Test
    void currentReadableFlagsTakePrecedenceOverHistoricalCompletion() throws IOException {
        Outcome ongoing = observeCase("current_precedes_history_ongoing");
        assertEquals(Status.ONGOING, ongoing.status()); assertTrue(ongoing.terminalFlagsObserved());
        assertTrue(ongoing.historicalObservation().isEmpty());
        Outcome unobserved = observeCase("current_precedes_history_unobserved");
        assertEquals(Status.UNKNOWN, unobserved.status());
        assertEquals(Optional.of(UnknownReason.TERMINAL_FLAGS_UNOBSERVED), unobserved.unknownReason());
        assertTrue(unobserved.historicalObservation().isEmpty());
        Outcome mismatch = observeCase("current_precedes_history_wrong_type");
        assertEquals(Optional.of(UnknownReason.ACTIVITY_IDENTITY_MISMATCH), mismatch.unknownReason());
    }

    @Test
    void partialHistoricalFlagsAndZeroStampNeverBecomeCompleteObservationOrUtility() throws IOException {
        Outcome partial = observeCase("history_partial_completed");
        assertEquals(Status.COMPLETED, partial.status()); assertFalse(partial.terminalFlagsObserved());
        assertEquals(BooleanObservation.TRUE, partial.completed()); assertEquals(BooleanObservation.UNKNOWN, partial.invalidated());
        assertTrue(partial.historicalObservation().isPresent());
        Outcome zero = observeCase("current_stamp_zero");
        assertEquals(Status.UNKNOWN, zero.status());
        assertEquals(new StampObserved(BigInteger.ZERO), zero.completionStamp());
        JsonNode wire = JSON.readTree(FeastTerminalCodec.encodeOutcome(zero));
        assertFalse(wire.has("benefit_verified")); assertFalse(wire.has("saved_days")); assertFalse(wire.has("action_authorized"));
    }

    @Test
    void preservesUint64AndSignedHostBitIdentityWithoutNumberRounding() throws IOException {
        Outcome original = observeCase("history_completed");
        assertEquals(new StampObserved(NativeTerminalJournal.MAX_U64), original.completionStamp());
        assertEquals(Long.MIN_VALUE, original.historicalObservation().orElseThrow().frame().dateRaw());
        String raw = rawCase("history_completed")
                .replace("\"actor_character_id\":29829", "\"actor_character_id\":4294967295")
                .replace("\"query_actor_full_id_u32\":29829", "\"query_actor_full_id_u32\":4294967295")
                .replace("\"host_character_id_i32\":29829", "\"host_character_id_i32\":-1")
                .replace("\"actor_character_id_i32\":29829", "\"actor_character_id_i32\":-1");
        Outcome unsigned = FeastTerminalPolicy.observe(decode(raw));
        assertEquals(4_294_967_295L, unsigned.actorId()); assertEquals(Status.COMPLETED, unsigned.status());
        assertEquals(-1, unsigned.historicalObservation().orElseThrow().hostCharacterId());
    }

    @Test
    void malformedOptionalJournalStaysUnavailableAndRawFloatTokensAreNotCoerced() throws IOException {
        for (String token : List.of("1.0", "1e0", "true", "\"1\"")) {
            String raw = rawCase("history_completed").replace("\"capture_sequence_u64\":1", "\"capture_sequence_u64\":" + token);
            Request request = decode(raw);
            assertInstanceOf(UnusableJournal.class, request.post().journal());
            Outcome outcome = FeastTerminalPolicy.observe(request);
            assertEquals(Status.UNKNOWN, outcome.status());
            JsonNode wire = JSON.readTree(FeastTerminalCodec.encodeOutcome(outcome));
            assertTrue(wire.get("native_terminal_observations_coverage").isNull());
        }
    }

    @Test
    void rejectsWrongRequestTokensDuplicatesUtf8TrailingAndByteOverflow() throws IOException {
        String baseline = rawCase("absent_activity");
        for (String token : List.of("16777234.0", "16777234e0", "true", "\"16777234\"", "null")) {
            String raw = baseline.replace("\"activity_id\":16777234", "\"activity_id\":" + token);
            assertThrows(IllegalArgumentException.class, () -> decode(raw), token);
        }
        assertThrows(IllegalArgumentException.class, () -> decode("{\"activity_id\":1," + baseline.substring(1)));
        assertThrows(IllegalArgumentException.class, () -> decode(baseline + " {}"));
        assertThrows(IllegalArgumentException.class, () -> FeastTerminalCodec.decodeRequest(new byte[] {(byte) 0xC3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> FeastTerminalCodec.decodeRequest(new byte[FeastTerminalCodec.MAX_INPUT_BYTES + 1]));
        assertThrows(IllegalArgumentException.class, () -> decode(baseline.replace("\"post\":", "\"unexpected\":0,\"post\":")));
    }

    @Test
    void immutableJournalAndOutcomeConstructorsRejectContradictoryPublicBranches() throws IOException {
        Request request = decode(rawCase("history_completed"));
        ParsedJournal journal = assertInstanceOf(ParsedJournal.class, request.post().journal());
        assertThrows(UnsupportedOperationException.class, () -> journal.value().records().clear());
        Outcome existing = FeastTerminalPolicy.observe(request);
        assertThrows(IllegalArgumentException.class, () -> new Outcome(existing.activityId(), existing.actorId(), existing.revision(),
                existing.dateRaw(), Status.ONGOING, true, BooleanObservation.TRUE, BooleanObservation.FALSE, Optional.empty(),
                existing.completionStamp(), Optional.empty(), existing.journalCoverage(), existing.provenance()));
        assertThrows(IllegalArgumentException.class, () -> new Request(0, request.actorId(), request.post()));
    }

    @Test
    void sdkPostExtensionsDoNotInheritTheSmallerLeafByteLimitOrExactKeySet() throws IOException {
        String baseline = rawCase("absent_activity");
        String extended = baseline.replace("\"read_only\":true", "\"read_only\":true,\"future_sdk_extension\":{\"opaque\":\"" + "x".repeat(300_000) + "\"}");
        assertTrue(extended.getBytes(StandardCharsets.UTF_8).length > 262_144);
        assertEquals(FeastTerminalPolicy.observe(decode(baseline)), FeastTerminalPolicy.observe(decode(extended)));
    }

    private static Request decode(String raw) { return FeastTerminalCodec.decodeRequest(raw.getBytes(StandardCharsets.UTF_8)); }
    private static Outcome observeCase(String name) throws IOException { return FeastTerminalPolicy.observe(decode(rawCase(name))); }
    private static String rawCase(String name) throws IOException {
        for (JsonNode row : golden().get("cases")) if (row.get("name").textValue().equals(name)) return row.get("input_json").textValue();
        throw new IOException("missing required original producer case " + name);
    }
    private static JsonNode golden() throws IOException {
        try (InputStream input = FeastTerminalPolicyTest.class.getResourceAsStream("/feastterminal/terminal-producer-golden-v1.json")) {
            if (input == null) throw new IOException("required actual terminal producer golden unavailable");
            return JSON.readTree(input.readAllBytes());
        }
    }
}
