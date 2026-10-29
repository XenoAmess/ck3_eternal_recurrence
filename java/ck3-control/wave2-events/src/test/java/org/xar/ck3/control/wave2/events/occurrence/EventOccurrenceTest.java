package org.xar.ck3.control.wave2.events.occurrence;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave2.events.occurrence.EventOccurrence.Request;
import org.xar.ck3.control.wave2.events.occurrence.EventOccurrence.Result;
import org.xar.ck3.control.wave2.events.occurrence.EventOccurrence.Status;
import org.xar.ck3.control.wave2.events.occurrence.HealthOccurrencePort.ReviewedSources;

final class EventOccurrenceTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static JsonNode golden() throws IOException {
        try (InputStream stream = EventOccurrenceTest.class.getResourceAsStream("/occurrence/event-occurrence-golden-v1.json")) {
            assertNotNull(stream, "actual original producer fixture is required; no skipped verification");
            return JSON.readTree(stream);
        }
    }
    private static Request decode(JsonNode row) throws IOException { return EventOccurrenceCodec.decode(JSON.writeValueAsBytes(row)); }
    private static ObjectNode baseline() throws IOException { return golden().get("cases").get(3).get("request").deepCopy(); }

    @Test void matchesOriginalTwoPassProducerForAllTwentyEightRetainedLineageCases() throws IOException {
        JsonNode corpus = golden();
        assertEquals("xar.ck3.event-occurrence-golden/v1", corpus.get("schema").textValue());
        assertEquals(28, corpus.get("cases").size());
        for (JsonNode row : corpus.get("cases")) {
            Result result = EventOccurrence.count(decode(row.get("request")));
            assertEquals(row.get("expected"), JSON.readTree(EventOccurrenceCodec.encode(result)), row.get("name").textValue());
            assertFalse(result.actionAuthorized());
        }
    }

    @Test void typedHistoryProjectionRoundTripsAndIsImmutable() throws IOException {
        for (JsonNode row : golden().get("cases")) {
            Request input = decode(row.get("request"));
            Request roundTrip = EventOccurrenceCodec.decode(EventOccurrenceCodec.encode(input));
            assertEquals(input, roundTrip);
            assertEquals(EventOccurrence.count(input), EventOccurrence.count(roundTrip));
            input.commands().ifPresent(rows -> assertThrows(UnsupportedOperationException.class, rows::clear));
        }
    }

    @Test void rawFloatBoolAndStringIdentityTokensAreRejectedBeforeCounting() throws IOException {
        String raw = new String(JSON.writeValueAsBytes(baseline()), StandardCharsets.UTF_8);
        assertTrue(raw.contains("\"queried_revision\":3"));
        for (String token : List.of("3.0", "true", "\"3\"")) {
            byte[] malformed = raw.replace("\"queried_revision\":3", "\"queried_revision\":" + token).getBytes(StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> EventOccurrenceCodec.decode(malformed));
        }
        byte[] nativeFloat = raw.replace("\"snapshot_revision\":7", "\"snapshot_revision\":7.0").getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> EventOccurrenceCodec.decode(nativeFloat));
        byte[] charBool = raw.replace("\"character_id\":29829", "\"character_id\":true").getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> EventOccurrenceCodec.decode(charBool));
        byte[] flagInteger = raw.replace("\"ok\":true", "\"ok\":1").getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> EventOccurrenceCodec.decode(flagInteger));
    }

    @Test void missingNullAndEmptyHistoryHaveDistinctRuntimeContracts() throws IOException {
        ObjectNode missing = baseline(); missing.remove("commands");
        byte[] missingBytes = JSON.writeValueAsBytes(missing);
        assertThrows(IllegalArgumentException.class, () -> EventOccurrenceCodec.decode(missingBytes));
        ObjectNode noHistory = baseline(); noHistory.putNull("commands");
        assertEquals(Status.UNAVAILABLE, EventOccurrence.count(decode(noHistory)).status());
        ObjectNode empty = baseline(); empty.putArray("commands");
        Result result = EventOccurrence.count(decode(empty));
        assertEquals(Status.AVAILABLE, result.status()); assertEquals(0, result.count());
        ObjectNode extension = baseline(); extension.put("unsafe_override", true);
        byte[] extensionBytes = JSON.writeValueAsBytes(extension);
        assertThrows(IllegalArgumentException.class, () -> EventOccurrenceCodec.decode(extensionBytes));
        ObjectNode legacyExtension = baseline();
        ((ObjectNode) legacyExtension.get("commands").get(0).get("result")).put("existing_native_diagnostic", "allowed producer extension");
        assertEquals(EventOccurrence.count(decode(baseline())), EventOccurrence.count(decode(legacyExtension)));
    }

    @Test void asciiCommandParserRetainsLeadingZerosAndRejectsUnicodeAndNonpositiveChoices() {
        assertEquals(Optional.of(BigInteger.TWO), EventOccurrence.parseOptionStep("select-event-option-0002"));
        assertEquals(Optional.empty(), EventOccurrence.parseOptionStep("select-event-option-２"));
        assertEquals(Optional.empty(), EventOccurrence.parseOptionStep("select-event-option-0"));
        assertEquals(Optional.empty(), EventOccurrence.parseOptionStep("select-event-option--1"));
        assertEquals(Optional.empty(), EventOccurrence.parseOptionStep("select-event-option-2 "));
        assertEquals(Optional.empty(), EventOccurrence.parseOptionStep(null));
    }

    @Test void health1015ConsumerPreservesSourcePlayerAndOccurrenceBoundWithoutActionAuthority() throws IOException {
        Result count = EventOccurrence.count(decode(baseline()));
        ReviewedSources sources = new ReviewedSources("74073E049A416C744B36A2A996FA467610705E38D53C836B050F1AC6F66E1212",
            "ABEFA738C913C660A52FA747BCC92FCA2F57D77A0F47D903BEDC2882F3D5A9DB");
        HealthOccurrencePort.Assessment ready = HealthOccurrencePort.assess(count, BigInteger.valueOf(29829), BigInteger.TWO, sources);
        assertTrue(ready.occurrenceBoundReady()); assertFalse(ready.actionAuthorized());
        assertFalse(HealthOccurrencePort.assess(count, BigInteger.valueOf(29829), BigInteger.ONE, sources).checks().get("max_occurrences"));
        assertFalse(HealthOccurrencePort.assess(count, BigInteger.valueOf(29829), BigInteger.TWO,
            new ReviewedSources(sources.healthEventsSha256().toLowerCase(java.util.Locale.ROOT), sources.healthEffectsSha256()))
            .checks().get("health1015_exact_source"));
        assertFalse(HealthOccurrencePort.assess(count, BigInteger.valueOf(999), BigInteger.TWO, sources).checks().get("occurrence_history_ready"));
        assertFalse(HealthOccurrencePort.assess(new Result("other.1", count.playedCharacterId(), Status.AVAILABLE, 0, null),
            count.playedCharacterId(), BigInteger.TWO, sources).checks().get("occurrence_history_ready"));
    }

    @Test void duplicateAndMalformedJsonCannotIntroduceASelection() throws IOException {
        String raw = new String(JSON.writeValueAsBytes(baseline()), StandardCharsets.UTF_8);
        String duplicate = raw.replace("\"played_character_id\":29829", "\"played_character_id\":29829,\"played_character_id\":29829");
        assertThrows(IllegalArgumentException.class, () -> EventOccurrenceCodec.decode(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> EventOccurrenceCodec.decode((raw + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> EventOccurrenceCodec.decode(new byte[] {(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> EventOccurrenceCodec.decode(new byte[1_048_577]));
    }
}
