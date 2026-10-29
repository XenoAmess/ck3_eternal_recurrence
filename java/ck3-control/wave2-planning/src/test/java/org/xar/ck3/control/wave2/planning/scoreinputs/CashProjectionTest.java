package org.xar.ck3.control.wave2.planning.scoreinputs;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.campaigncadence.MonthlyObservation.Metric;
import org.xar.ck3.control.wave2.finance.rawcash.SdkProjectionJson;

final class CashProjectionTest {
    @Test void actualProducerTupleMatchesSharedRawCashDecoderAndFourRateMapping() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.ck3.java-cashmetrics-producer-golden/v1", golden.path("schema").asText());
        assertEquals(12, golden.path("cases").size());
        int rejected = 0;
        for (JsonNode row : golden.path("cases")) {
            byte[] raw = new ObjectMapper().writeValueAsBytes(row.get("request"));
            if (row.path("expected").path("status").asText().equals("rejected")) {
                assertThrows(IllegalArgumentException.class, () -> CashMetricsCodec.evaluate(raw), row.path("id").asText());
                rejected++;
            } else {
                assertEquals(row.path("expected").get("value"), StrictJson.parse(CashMetricsCodec.evaluate(raw)), row.path("id").asText());
            }
        }
        assertTrue(rejected >= 6);
    }

    @Test void actorGlobalExpenseIsCountedOnceAndPartialPersonalRatesRemainUnknown() throws IOException {
        CashProjection base = decode("retained-cash");
        CashProjection twoWars = decode("two-wars-one-global-cost");
        assertEquals(base.metrics(), twoWars.metrics());
        assertEquals("9.93374", ((CashProjection.Observed) base.metrics().get(Metric.GROSS_INCOME)).valueText());
        assertEquals("0.111", ((CashProjection.Observed) base.metrics().get(Metric.MILITARY_CURRENT)).valueText());
        CashProjection partial = decode("partial-total-and-net");
        assertInstanceOf(CashProjection.Unknown.class, partial.metrics().get(Metric.TOTAL_EXPENSES));
        assertInstanceOf(CashProjection.Observed.class, partial.metrics().get(Metric.GROSS_INCOME));
        assertInstanceOf(CashProjection.Observed.class, partial.metrics().get(Metric.MILITARY_CURRENT));
        assertTrue(partial.metrics().get(Metric.TOTAL_EXPENSES).toJson().get("value").isNull());
    }

    @Test void incompatibleMilitaryRateNeverBecomesKnownZeroOrAValidBudget() throws IOException {
        CashProjection projection = decode("military-exceeds-total");
        CashProjection.Unknown current = assertInstanceOf(CashProjection.Unknown.class, projection.metrics().get(Metric.MILITARY_CURRENT));
        assertEquals(CashProjection.UnknownReason.MILITARY_EXCEEDS_TOTAL, current.reason());
        assertEquals("cash_military_exceeds_compatible_total_expenses", current.toJson().path("reason_zh").asText());
        assertInstanceOf(CashProjection.Observed.class, projection.metrics().get(Metric.TOTAL_EXPENSES));
    }

    @Test void packetAndPublicResultAreDefensiveAndSerializationIsTheAgreedTupleList() throws IOException {
        ObjectNode request = request("retained-cash");
        byte[] raw = new ObjectMapper().writeValueAsBytes(request);
        byte[] before = raw.clone();
        CashProjection projection = CashMetricsCodec.decode(raw);
        assertTrue(java.util.Arrays.equals(before, raw));
        assertThrows(UnsupportedOperationException.class, () -> projection.metrics().clear());
        String originalVersion = projection.source().monthlyIncomeSemantics().path("version").asText();
        projection.source().monthlyIncomeSemantics().put("version", "changed");
        assertEquals(originalVersion, projection.source().monthlyIncomeSemantics().path("version").asText());
        JsonNode encoded = StrictJson.parse(StrictJson.canonical(projection.toJson()));
        assertTrue(encoded.isArray()); assertEquals(2, encoded.size());
        assertEquals(encoded, StrictJson.parse(CashMetricsCodec.evaluate(before)));
    }

    @Test void wrongNumericTokensGoThroughActualSharedValidatorWithoutIntegerCoercion() throws IOException {
        for (String field : List.of("played_character_id", "snapshot_revision", "date_raw", "queried_revision", "queried_native_revision")) {
            String validInteger = request("retained-cash").path("packet").path(field).bigIntegerValue().toString();
            for (String token : List.of("true", validInteger + ".0", "\"" + validInteger + "\"")) {
                ObjectNode request = request("retained-cash");
                ((ObjectNode) request.get("packet")).put(field, "__raw_token__");
                String rawText = new ObjectMapper().writeValueAsString(request).replace("\"__raw_token__\"", token);
                assertTrue(rawText.contains("\"" + field + "\":" + token), "the exact original token must reach the outer entry");
                assertThrows(IllegalArgumentException.class, () -> CashMetricsCodec.evaluate(bytes(rawText)), field + ":" + token);
            }
        }
        ObjectNode extension = request("retained-cash");
        ((ObjectNode) extension.get("packet")).put("sdk_extension", 1.0);
        assertEquals(decode("retained-cash").metrics(), CashMetricsCodec.decode(new ObjectMapper().writeValueAsBytes(extension)).metrics());
        JsonNode extensionReparsed = StrictJson.parse(SdkProjectionJson.encode(StrictJson.parse(new ObjectMapper().writeValueAsBytes(extension))));
        assertTrue(extensionReparsed.path("packet").path("sdk_extension").isFloatingPointNumber());
    }

    @Test void strictRequestRefusesUnknownMissingNullAndDuplicateFields() {
        for (String input : List.of("{\"packet\":{}}", "{\"packet\":null,\"snapshot\":null}",
                "{\"packet\":{},\"snapshot\":{},\"extra\":false}", "{\"packet\":{},\"packet\":{},\"snapshot\":{}}")) {
            assertThrows(IllegalArgumentException.class, () -> CashMetricsCodec.evaluate(bytes(input)));
        }
    }

    private static JsonNode golden() throws IOException {
        try (InputStream stream = CashProjectionTest.class.getResourceAsStream("/scoreinputs/cash-producer-golden.json")) {
            if (stream == null) { throw new IOException("actual _cash_metrics producer golden required; never skip"); }
            byte[] raw = stream.readAllBytes();
            JsonNode document = StrictJson.parse(raw);
            CashMetricsGoldenCapture.validateOutput(raw, document.path("machine_id").asText());
            return document;
        }
    }
    private static ObjectNode request(String id) throws IOException {
        for (JsonNode row : golden().path("cases")) {
            if (id.equals(row.path("id").asText())) { return ((ObjectNode) row.get("request")).deepCopy(); }
        }
        throw new IOException("actual cash producer case missing: " + id);
    }
    private static CashProjection decode(String id) throws IOException { return CashMetricsCodec.decode(new ObjectMapper().writeValueAsBytes(request(id))); }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}
