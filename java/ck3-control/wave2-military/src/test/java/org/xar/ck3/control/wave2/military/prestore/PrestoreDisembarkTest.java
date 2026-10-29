package org.xar.ck3.control.wave2.military.prestore;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.io.ByteArrayInputStream;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.countyentry.CountyEntryCodec;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

final class PrestoreDisembarkTest {
    private static JsonNode golden() throws IOException {
        try (var stream = PrestoreDisembarkTest.class.getResourceAsStream("/prestore/original-producer-golden.json.gz")) {
            assertNotNull(stream, "managed original producer capture is required; missing is failure, not skip");
            byte[] compressed = stream.readNBytes(98_305);
            if (compressed.length > 98_304) { throw new IOException("prestore gzip exceeds 96 KiB fixture budget"); }
            try (var input = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
                return StrictJson.parse(input.readNBytes(262_145), 262_144);
            }
        }
    }
    private static byte[] bytes(JsonNode node) { return StrictJson.canonical(node, 110_000); }
    private static byte[] raw(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static ObjectNode expected(JsonNode sample, JsonNode golden) {
        ObjectNode expected = (ObjectNode) sample.get("expected_top").deepCopy();
        expected.set("county_entry_risk_v1", golden.get("county_risks").get(sample.get("county_risk_index").intValue())); return expected;
    }

    @Test void actualOriginalServiceHelperOutputsMatchTheCompleteJavaConsumer() throws IOException {
        JsonNode golden = golden(); assertFalse(golden.get("machine_id").textValue().isBlank());
        for (JsonNode sample : golden.get("cases")) {
            var input = PrestoreCodec.decode(bytes(sample.get("input"))); var result = PrestoreDisembark.project(input);
            assertEquals(StrictJson.parse(bytes(expected(sample, golden))), StrictJson.parse(PrestoreCodec.encode(result)), sample.get("id").textValue());
            assertEquals(StrictJson.parse(bytes(PrestoreCodec.node(result))), StrictJson.parse(PrestoreCodec.encode(result)));
            assertFalse(PrestoreCodec.node(result).get("native_action_executed").booleanValue());
            assertFalse(PrestoreCodec.node(result).get("actual_fixed_disembark_write_observed").booleanValue());
        }
    }

    @Test void sameQueryJoinConsumesTheActualSourceTupleAndRejectsDrift() throws IOException {
        JsonNode golden = golden();
        for (JsonNode sample : golden.get("cases")) {
            JsonNode input = sample.get("input");
            var source = CountyEntryCodec.decodeProvenance(sample.get("query"), true);
            var joined = PrestoreCodec.decodeSameQuery(input.get("strength"), input.get("arrival_transition"), input.get("movement_prefix"),
                    source, CountyEntryCodec.decodeQueryFrame(sample.get("snapshot")));
            var result = PrestoreDisembark.project(joined);
            assertEquals(StrictJson.parse(bytes(expected(sample, golden))), StrictJson.parse(PrestoreCodec.encode(result)), sample.get("id").textValue());
            assertEquals(sample.get("expected_service_provenance"), StrictJson.parse(bytes(PrestoreCodec.serviceRow(result, source).get("source_provenance"))));
            if (sample.get("id").textValue().equals("context_drift")) { assertEquals(null, joined.context()); }
        }
    }

    @Test void fullMovementNormalizerMatchesOriginalProducerAndRoundTripsPresence() throws IOException {
        for (JsonNode sample : golden().get("movements")) {
            var value = CurrentMovementCodec.normalize(bytes(sample.get("input")));
            assertEquals(sample.get("expected"), StrictJson.parse(CurrentMovementCodec.encode(value)), sample.get("id").textValue());
            assertEquals(value, CurrentMovementCodec.normalize(CurrentMovementCodec.encode(value)));
        }
    }

    @Test void rawTokenWidthAndTypeFailuresExecuteTheRealMovementBoundary() throws IOException {
        for (JsonNode sample : golden().get("rejections")) {
            assertThrows(IllegalArgumentException.class, () -> CurrentMovementCodec.normalize(raw(sample.get("raw_json").textValue())), sample.get("id").textValue());
        }
    }

    @Test void currentRemainingDaysDoNotSelectFixedWriteValue() throws IOException {
        JsonNode golden = golden(); JsonNode baseline = golden.get("cases").get(0);
        ObjectNode input = (ObjectNode) baseline.get("input").deepCopy();
        ((ObjectNode) input.get("strength").get("current_disembark_penalty_v1")).put("remaining_days", -999);
        var result = PrestoreDisembark.project(PrestoreCodec.decode(bytes(input)));
        assertTrue(result.selection().ready()); assertEquals(18, result.selection().writeValue());
        assertEquals(-999, PrestoreCodec.node(result).get("observed_current_disembark_penalty_existing").get("remaining_days").intValue());
    }

    @Test void legacyFloatingScaleEqualityIsTightenedOnlyAtTheDeclaredIntegerScale() throws IOException {
        JsonNode minimal = golden().get("movements").get(0).get("input");
        String original = new String(bytes(minimal), StandardCharsets.UTF_8);
        String malformed = original.replace("\"scale\":100000", "\"scale\":100000.0");
        assertFalse(original.equals(malformed));
        assertThrows(IllegalArgumentException.class, () -> CurrentMovementCodec.normalize(raw(malformed)));
    }
}
