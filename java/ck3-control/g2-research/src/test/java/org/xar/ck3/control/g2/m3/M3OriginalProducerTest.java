package org.xar.ck3.control.g2.m3;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.wave2.governance.succession.SuccessionFreshnessCodec;
import org.xar.ck3.control.wave2.governance.succession.SuccessionFreshnessPolicy;

/** Submitted original producer goldens only. Missing capture is RED; default tests never start Python. */
final class M3OriginalProducerTest {
    private static final String RESOURCE = "/g2/m3/original-producer-golden.json";
    private static final ObjectMapper JSON = JsonMapper.builder()
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS, DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .disable(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES).build();
    private record Golden(JsonNode value, byte[] bytes) {
        private Golden { bytes = bytes.clone(); }
        @Override public byte[] bytes() { return bytes.clone(); }
    }

    @Test void actualOriginalProducerAndAllRegisteredConsumersMatchThroughDomain() throws Exception {
        Golden golden = golden(); G2Source source = source(golden); M3Research domain = new M3Research();
        int count = 0;
        for (String group : new String[]{"producer_cases", "freshness_cases", "consumer_cases"}) {
            JsonNode cases = golden.value().get(group);
            assertNotNull(cases, "original capture must provide " + group);
            assertTrue(cases.isArray() && !cases.isEmpty(), group + " cannot pass as an empty or skipped producer seam");
            for (JsonNode vector : cases) {
                byte[] requestBytes = bytes(vector.get("request")); byte[] preserved = requestBytes.clone();
                String id = "m3-" + count++;
                G2Request request = new G2Request(id, Milestone.M3, source,
                        ProjectionJson.object(requestBytes, M3Research.MAXIMUM_BYTES));
                G2Response result = domain.evaluate(request);
                assertEquals(id, result.requestId()); assertEquals(Milestone.M3, result.milestone());
                assertEquals(source, result.source(), "domain preserves the exact caller-issued source envelope");
                assertEquals(vector.get("expected"), JSON.readTree(result.result().bytes()), group + ":" + vector.path("name").asText());
                assertArrayEquals(preserved, request.payload().bytes(), "input evidence is immutable");
            }
        }
        assertTrue(count > 0);
    }

    @Test void originalRejectedInputsStayRejectedThroughTheSameDomainRoute() throws Exception {
        Golden golden = golden(); G2Source source = source(golden); M3Research domain = new M3Research();
        for (String group : new String[]{"producer_rejected", "freshness_rejected", "consumer_rejected"}) {
            JsonNode cases = golden.value().get(group);
            assertNotNull(cases, "capture must preserve original failures for " + group);
            assertTrue(cases.isArray() && !cases.isEmpty(), group);
            for (JsonNode vector : cases) {
                assertFalse(vector.path("error_type").asText().isBlank(), "preserve actual original error type");
                G2Request request = new G2Request("m3-reject", Milestone.M3, source,
                        ProjectionJson.object(bytes(vector.get("request")), M3Research.MAXIMUM_BYTES));
                assertThrows(IllegalArgumentException.class, () -> domain.evaluate(request),
                        group + ":" + vector.path("name").asText());
            }
        }
    }

    @Test void freshnessConsumedProjectionSurvivesPersistenceAndCannotGrantCredit() throws Exception {
        Set<String> states = new HashSet<>(); boolean historical3121And7 = false;
        for (JsonNode vector : golden().value().path("freshness_cases")) {
            byte[] request = bytes(vector.get("request"));
            var typed = SuccessionFreshnessCodec.decode(request);
            JsonNode actual = JSON.readTree(SuccessionFreshnessCodec.encode(SuccessionFreshnessPolicy.observe(typed)));
            assertEquals(vector.get("expected"), actual, vector.path("name").asText());
            byte[] persisted = SuccessionFreshnessCodec.encodeRequest(typed);
            assertEquals(actual, JSON.readTree(SuccessionFreshnessCodec.observe(persisted)),
                    "JSON roundtrip compares the declared consumed projection, including explicit nulls");
            states.add(actual.path("all_title_freshness").asText());
            for (String flag : new String[]{"fresh_immediately_before_death_claimed", "reconciliation_verified_by_this_observer",
                    "process_birth_verified_by_this_observer", "replay_allowed", "business_credit", "M7_coverage_credit"}) {
                assertTrue(actual.get(flag).isBoolean()); assertFalse(actual.get(flag).booleanValue(), flag);
            }
            if (decimalEquals(actual.get("expectation_age_days_at_boundary"), "3121")
                    && decimalEquals(actual.get("last_observed_living_age_days_at_boundary"), "7")) {
                historical3121And7 = true;
                assertEquals("full_expectation_not_observed", actual.path("all_title_freshness").asText());
                assertTrue(actual.get("complete_title_ids").isNull());
                assertFalse(actual.path("complete_title_expectation_observed").asBoolean());
            }
        }
        assertEquals(Set.of("full_expectation_not_observed", "last_living_frame_not_observed",
                "same_as_last_observed_living_frame", "different_from_last_observed_living_frame"), states);
        assertTrue(historical3121And7, "preserve the actual small 3121/7-day evidence without inventing full-title freshness");
    }

    @Test void rawWrongTypesMissingNullAndEmptyReachTheStrictBoundary() throws Exception {
        ObjectNode base = golden().value().path("freshness_cases").get(0).get("request").deepCopy();
        for (String token : new String[]{"true", "3.0", "\"3\"", "null", "-1"}) {
            ObjectNode changed = base.deepCopy();
            ObjectNode binding = (ObjectNode) changed.path("reconciliation").path("predecessor_binding");
            binding.set("revision", JSON.readTree(token));
            assertThrows(IllegalArgumentException.class, () -> SuccessionFreshnessCodec.observe(bytes(changed)), token);
        }
        ObjectNode missing = base.deepCopy(); missing.remove("expectation");
        assertThrows(IllegalArgumentException.class, () -> SuccessionFreshnessCodec.observe(bytes(missing)));
        ObjectNode empty = base.deepCopy(); empty.set("expectation", JSON.createObjectNode());
        assertThrows(IllegalArgumentException.class, () -> SuccessionFreshnessCodec.observe(bytes(empty)));
        ObjectNode emptyLiving = base.deepCopy(); emptyLiving.set("last_living_frame", JSON.createObjectNode());
        assertThrows(IllegalArgumentException.class, () -> SuccessionFreshnessCodec.observe(bytes(emptyLiving)));
        ObjectNode extra = base.deepCopy(); extra.put("ready", true);
        assertThrows(IllegalArgumentException.class, () -> SuccessionFreshnessCodec.observe(bytes(extra)));
        String duplicate = new String(bytes(base), StandardCharsets.UTF_8);
        duplicate = duplicate.substring(0, duplicate.length() - 1) + ",\"schema\":\"duplicate\"}";
        byte[] duplicated = duplicate.getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> SuccessionFreshnessCodec.observe(duplicated));
        byte[] trailing = (new String(bytes(base), StandardCharsets.UTF_8) + " {}").getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> SuccessionFreshnessCodec.observe(trailing));
        assertThrows(IllegalArgumentException.class, () -> SuccessionFreshnessCodec.observe(new byte[]{(byte) 0xc3, 0x28}));
    }

    @Test void routeCannotRebindMilestoneOrInventAnActionSchema() throws Exception {
        Golden golden = golden(); M3Research domain = new M3Research(); G2Source source = source(golden);
        byte[] input = bytes(golden.value().path("freshness_cases").get(0).get("request"));
        assertThrows(IllegalArgumentException.class, () -> domain.evaluate(new G2Request("wrong-milestone", Milestone.M0,
                source, ProjectionJson.object(input, M3Research.MAXIMUM_BYTES))));
        for (String schema : new String[]{"Continue", "Close", "SAVE", "resident_successor_ui_pending"}) {
            ObjectNode value = JSON.createObjectNode(); value.put("schema", schema);
            assertThrows(IllegalArgumentException.class, () -> domain.evaluate(new G2Request("no-action", Milestone.M3,
                    source, ProjectionJson.object(bytes(value), M3Research.MAXIMUM_BYTES))));
        }
    }

    private static Golden golden() throws IOException {
        try (InputStream input = M3OriginalProducerTest.class.getResourceAsStream(RESOURCE)) {
            assertNotNull(input, "actual original producer/consumer capture is mandatory; never skip or launch Python");
            byte[] raw = input.readAllBytes(); JsonNode value = JSON.readTree(raw);
            assertEquals("xar.g2.m3.original-producer-golden/v1", value.path("schema").asText());
            assertTrue(value.path("synthetic_fixture").asBoolean(), "the backend is an explicit software fixture");
            assertTrue(value.path("source_refs_unchanged").asBoolean());
            assertFalse(value.path("machine_id").asText().isBlank());
            assertFalse(value.path("observed_at_utc").asText().isBlank());
            return new Golden(value, raw);
        }
    }
    private static G2Source source(Golden golden) throws Exception {
        String sha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(golden.bytes()));
        return new G2Source(golden.value().path("machine_id").asText(), golden.value().path("observed_at_utc").asText(),
                "offline-original-producer-fixture", new ExactRef(RESOURCE, golden.bytes().length, sha));
    }
    private static boolean decimalEquals(JsonNode value, String expected) {
        return value != null && value.isNumber() && value.decimalValue().compareTo(new BigDecimal(expected)) == 0;
    }
    private static byte[] bytes(JsonNode value) throws IOException { return JSON.writeValueAsBytes(value); }
}
