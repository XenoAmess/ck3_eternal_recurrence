package org.xar.ck3.control.planning.campaigncadence;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

final class CampaignCadenceTest {
    private static final String RESOURCE = "/campaigncadence/producer-golden.json";

    @Test void actualProducerGoldenIncludesEveryPureApiAndExactRequestRoundTrips() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.ck3.java-campaign-cadence-producer-golden/v1", golden.path("schema").asText());
        assertTrue(golden.path("cases").size() >= 28, "real producer capture must be present");
        int returned = 0;
        int rejected = 0;
        for (JsonNode row : golden.path("cases")) {
            JsonNode request = row.get("request");
            if (row.path("expected").path("status").asText().equals("rejected")) {
                assertThrows(IllegalArgumentException.class,
                        () -> CampaignCadenceCodec.decode(StrictJson.canonical(request)).evaluate(), row.path("id").asText());
                rejected++;
            } else {
                CampaignCadenceCodec.Request decoded = CampaignCadenceCodec.decode(StrictJson.canonical(request));
                assertEquals(row.path("expected").get("value"), normalized(decoded.evaluate()), row.path("id").asText());
                CampaignCadenceCodec.Request restored = CampaignCadenceCodec.decode(CampaignCadenceCodec.encode(decoded));
                assertEquals(decoded, restored, row.path("id").asText());
                assertEquals(normalized(decoded.evaluate()), StrictJson.parse(CampaignCadenceCodec.evaluate(CampaignCadenceCodec.encode(restored))));
                returned++;
            }
        }
        assertTrue(returned >= 20);
        assertTrue(rejected >= 4);
    }

    @Test void fixedCalendarHasNoGregorianLeapDayAndMonthClampNeverDrifts() {
        assertEquals(53144328, CampaignCalendar.dateToRaw("1066.9.15"));
        assertEquals(53407128, CampaignCalendar.dateToRaw("1096.9.15"));
        assertEquals(24, CampaignCalendar.dateToRaw("1068.3.1") - CampaignCalendar.dateToRaw("1068.2.28"));
        List<CampaignCalendar.Boundary> boundaries = CampaignCalendar.monthBoundaries("1068.1.31", 2);
        assertEquals(List.of("1068.1.31", "1068.2.28", "1068.3.31"), boundaries.stream().map(CampaignCalendar.Boundary::date).toList());
        assertThrows(UnsupportedOperationException.class, () -> boundaries.clear());
        List<CampaignCalendar.Boundary> thirtyYears = CampaignCalendar.monthBoundaries("1066.9.15", 360);
        assertEquals(361, thirtyYears.size());
        assertSame(thirtyYears, CampaignCalendar.monthBoundaries("1066.9.15", 360));
        assertEquals(10950, (thirtyYears.getLast().raw() - thirtyYears.getFirst().raw()) / 24);
        assertEquals(361, thirtyYears.stream().map(CampaignCalendar.Boundary::raw).distinct().count());
    }

    @Test void missedSlotsStayMissingAndEndpointNeverBecomesAnAdvance() {
        CampaignAdvanceCap cap = CampaignAdvanceCap.plan(CampaignCalendar.dateToRaw("1066.10.16"),
                CampaignCalendar.dateToRaw("1066.10.24"), "1066.9.15", 1, 360);
        assertEquals(List.of(1), cap.missedSampleIndices());
        assertEquals(2, cap.nextSampleIndex());
        assertEquals(CampaignAdvanceCap.Status.ADVANCE, cap.status());
        assertEquals(0, cap.toJson().path("new_clock_actions").intValue());
        CampaignAdvanceCap end = CampaignAdvanceCap.plan(53407128, 53407152, "1066.9.15", 360, 360);
        assertEquals(CampaignAdvanceCap.Status.ENDPOINT_DUE, end.status());
        assertTrue(end.toJson().get("target_date_raw").isNull());
        assertFalse(end.toJson().has("boundary_date_raw"));
    }

    @Test void exactIntegerTokensRejectBooleanFloatStringNullMissingAndUnknownFields() {
        for (String token : List.of("true", "53144328.0", "\"53144328\"", "null", "2147483648")) {
            assertThrows(IllegalArgumentException.class,
                    () -> CampaignCadenceCodec.decode(bytes("{\"operation\":\"raw_to_date\",\"raw\":" + token + "}")));
        }
        assertThrows(IllegalArgumentException.class, () -> CampaignCadenceCodec.decode(bytes("{\"operation\":\"raw_to_date\"}")));
        assertThrows(IllegalArgumentException.class, () -> CampaignCadenceCodec.decode(bytes("{\"operation\":\"raw_to_date\",\"raw\":53144328,\"extra\":0}")));
        assertThrows(IllegalArgumentException.class, () -> CampaignCadenceCodec.decode(bytes("{\"operation\":\"raw_to_date\",\"raw\":53144328,\"raw\":53144328}")));
        assertThrows(IllegalArgumentException.class, () -> CampaignCadenceCodec.decode(new byte[] {(byte) 0xc3, (byte) 0x28}));
    }

    @Test void nullableFieldsEmptyWarsAndUnknownWarsKeepDifferentMeanings() throws IOException {
        ObjectNode withEmptyWars = candidateRequest("sample-negative-gold");
        ObjectNode output = (ObjectNode) CampaignCadenceCodec.decode(withEmptyWars).evaluate();
        assertTrue(output.get("observed_player_wars").isArray());
        assertTrue(output.get("observed_player_wars").isEmpty());
        assertTrue(output.path("frame").get("one_life_terminal").isNull());
        ((ObjectNode) withEmptyWars.get("snapshot")).remove("active_wars");
        ObjectNode unknown = (ObjectNode) CampaignCadenceCodec.decode(withEmptyWars).evaluate();
        assertTrue(unknown.get("observed_player_wars").isNull());
        assertNotEquals(output, unknown);
        assertEquals("-0.12345", output.path("raw_metrics").path("gold").path("value").asText());
        assertEquals("unknown", output.path("raw_metrics").path("continuation_legal").path("availability").asText());
        assertFalse(output.path("score_or_complete_history_claimed").booleanValue());
        assertTrue(output.path("source_response_binding_pending").booleanValue());
    }

    @Test void projectedIdentityTypesAndNullabilityAreValidatedWithoutCoercion() throws IOException {
        ObjectNode request = candidateRequest("sample-negative-gold");
        ObjectNode snapshot = (ObjectNode) request.get("snapshot");
        for (JsonNode bad : List.of(JsonNodeFactory.instance.booleanNode(true), JsonNodeFactory.instance.numberNode(41.0),
                JsonNodeFactory.instance.textNode("41"), JsonNodeFactory.instance.nullNode(),
                JsonNodeFactory.instance.numberNode(new BigInteger("18446744073709551616")))) {
            snapshot.set("revision", bad);
            assertThrows(IllegalArgumentException.class, () -> CampaignCadenceCodec.decode(request).evaluate());
        }
        snapshot.put("revision", 41);
        snapshot.put("paused", "true");
        assertThrows(IllegalArgumentException.class, () -> CampaignCadenceCodec.decode(request).evaluate());
        snapshot.put("paused", true);
        ((ObjectNode) request.get("campaign_anchor")).put("founder_character_id", true);
        assertThrows(IllegalArgumentException.class, () -> CampaignCadenceCodec.decode(request).evaluate());
    }

    @Test void candidateInputAndReturnedSnapshotsCannotBeMutatedAfterDecoding() throws IOException {
        ObjectNode request = candidateRequest("sample-negative-gold");
        CampaignCadenceCodec.Candidate candidate = (CampaignCadenceCodec.Candidate) CampaignCadenceCodec.decode(request);
        JsonNode expected = candidate.evaluate();
        ((ObjectNode) request.get("snapshot")).put("date_raw", 1);
        candidate.snapshot().put("date_raw", 2);
        candidate.campaignAnchor().put("campaign_id", "changed");
        assertEquals(expected, candidate.evaluate());
        assertEquals(0, expected.path("new_RPC_calls").intValue());
        assertEquals(0, expected.path("new_SAVE_exports").intValue());
    }

    @Test void successorKeepsFoundingAnchorAndNonBoundaryCannotFabricateHistory() throws IOException {
        JsonNode first = CampaignCadenceCodec.decode(candidateRequest("sample-negative-gold")).evaluate();
        JsonNode second = CampaignCadenceCodec.decode(candidateRequest("sample-successor")).evaluate();
        assertEquals(first.get("campaign_anchor"), second.get("campaign_anchor"));
        assertNotEquals(first.path("frame").get("actor_character_id"), second.path("frame").get("actor_character_id"));
        assertEquals(first.get("baseline_date_raw"), second.get("baseline_date_raw"));
        assertTrue(CampaignCadenceCodec.decode(candidateRequest("sample-nonboundary")).evaluate().isNull());
    }

    @Test void unusedFiniteUpstreamDecimalsSurviveRequestRoundTripWithoutAffectingProjection() throws IOException {
        ObjectNode request = candidateRequest("sample-negative-gold");
        JsonNode baseline = CampaignCadenceCodec.decode(request).evaluate();
        ((ObjectNode) request.get("snapshot")).set("unconsumed_native_ratio",
                StrictJson.parse(bytes("0.12345678901234567890123456789")));
        CampaignCadenceCodec.Request decoded = CampaignCadenceCodec.decode(request);
        CampaignCadenceCodec.Request restored = CampaignCadenceCodec.decode(CampaignCadenceCodec.encode(decoded));
        assertEquals(decoded, restored);
        assertEquals(baseline, restored.evaluate());
        ((ObjectNode) request.get("snapshot")).put("unconsumed_native_ratio", Double.NaN);
        assertThrows(IllegalArgumentException.class, () -> CampaignCadenceCodec.encode(CampaignCadenceCodec.decode(request)));
    }

    private static JsonNode golden() throws IOException {
        try (InputStream stream = CampaignCadenceTest.class.getResourceAsStream(RESOURCE)) {
            if (stream == null) { throw new IOException("real producer golden missing; capture is required, never skipped"); }
            return StrictJson.parse(stream.readAllBytes());
        }
    }
    private static ObjectNode candidateRequest(String id) throws IOException {
        for (JsonNode row : golden().path("cases")) {
            if (id.equals(row.path("id").asText())) { return ((ObjectNode) row.get("request")).deepCopy(); }
        }
        throw new IOException("required producer case missing: " + id);
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static JsonNode normalized(JsonNode value) { return StrictJson.parse(StrictJson.canonical(value)); }
}
