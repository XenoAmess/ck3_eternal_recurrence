package org.xar.ck3.control.wave2.military.coalition;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.coalition.PrewarCoalition.Observation;

final class CoalitionRiskTest {
    private static final String GOLDEN = "/coalition/original-producer-golden01.json";

    @Test
    void realOriginalProducerGoldenAcrossAllCurrentContractBranches() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.coalition.original-producer-golden/v1", golden.path("schema").textValue());
        assertFalse(golden.path("machine_id").asText().isBlank());
        assertTrue(golden.path("source_refs").size() >= 10);
        int accepted = 0;
        int rejected = 0;
        for (JsonNode sample : golden.path("cases")) {
            ObjectNode request = golden.path("base").deepCopy();
            for (JsonNode edit : sample.path("edits")) applyEdit(request, edit);
            ObjectNode untouched = request.deepCopy();
            JsonNode expected = sample.path("expected");
            String id = sample.path("id").textValue();
            if (!expected.path("accepted").booleanValue()) {
                assertThrows(IllegalArgumentException.class, () -> assess(request), id);
                rejected++;
            } else {
                CoalitionRiskJsonAdapter.Assessment result = assess(request);
                assertEquals(canonical(expected.get("risk")), canonical(result.riskJson()), id);
                Boolean expectedCanSend = expected.get("final_can_send").isNull() ? null : expected.get("final_can_send").booleanValue();
                assertEquals(expectedCanSend, result.finalCanSend(), id);
                Observation observation = normalize(request);
                ObjectNode encoded = CoalitionRiskJsonAdapter.encodeObservation(observation);
                if (expected.has("normalized")) assertEquals(canonical(expected.get("normalized")), canonical(encoded), id);
                request.set("domain", StrictJson.parse(StrictJson.canonical(encoded)));
                assertEquals(observation, normalize(request), "typed JSON round trip: " + id);
                assertThrows(UnsupportedOperationException.class, () -> observation.ownerForces().clear(), id);
                assertThrows(UnsupportedOperationException.class, () -> observation.selectedDeclaration().targetTitleIds().clear(), id);
                assertThrows(UnsupportedOperationException.class, () -> observation.missingRequiredDomains().clear(), id);
                // Restore the input only after proving emitted wire preserves the typed record exactly.
                request.set("domain", untouched.get("domain"));
                accepted++;
            }
            assertEquals(untouched, request, "strict adapter mutated input: " + id);
        }
        assertTrue(accepted >= 20, "actual valid branch samples required");
        assertTrue(rejected >= 70, "actual malformed and stale branch samples required");
    }

    @Test
    void rawFloatTokensNeverBecomeIntegralThroughSerialization() throws IOException {
        ObjectNode request = golden().path("base").deepCopy();
        ObjectNode domain = (ObjectNode) request.get("domain");
        for (String token : new String[] {"2.0", "2e0", "true", "\"2\""}) {
            domain.set("schema_version", StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> assess(request), token);
        }
    }

    @Test
    void sdkExtensionProjectionRetainsOrderedTitlesAndDoesNotInventOuterLease() throws IOException {
        ObjectNode request = golden().path("base").deepCopy();
        Observation observation = normalize(request);
        ((ObjectNode) request.get("snapshot")).put("unrelated_snapshot_extension", 42);
        assertEquals(observation, normalize(request));
        assertTrue(CoalitionRiskJsonAdapter.isCurrent(request.get("domain"), request.get("snapshot"), request.get("declaration"),
                request.get("receipt"), request.get("request_id").textValue(), null));
        ((ObjectNode) request.get("receipt")).put("request_id", "stale-request");
        assertFalse(CoalitionRiskJsonAdapter.isCurrent(request.get("domain"), request.get("snapshot"), request.get("declaration"),
                request.get("receipt"), request.get("request_id").textValue(), null));
        assertEquals(1500L, observation.actorLowerSoldiers());
    }

    private static JsonNode golden() throws IOException {
        try (InputStream input = CoalitionRiskTest.class.getResourceAsStream(GOLDEN)) {
            assertNotNull(input, "committed original producer golden required; missing fixture is a failure");
            return StrictJson.parse(input.readAllBytes(), 81_920);
        }
    }

    private static CoalitionRiskJsonAdapter.Assessment assess(ObjectNode request) {
        return CoalitionRiskJsonAdapter.assess(request.get("domain"), request.get("snapshot"), request.get("declaration"),
                request.get("receipt"), request.get("request_id").textValue(), epoch(request), request.get("policy"));
    }

    private static Observation normalize(ObjectNode request) {
        return CoalitionRiskJsonAdapter.normalize(request.get("domain"), request.get("snapshot"), request.get("declaration"),
                request.get("receipt"), request.get("request_id").textValue(), epoch(request));
    }

    private static BigInteger epoch(ObjectNode request) {
        JsonNode value = request.get("expected_capture_epoch");
        return value.isNull() ? null : StrictJson.integer(value, BigInteger.ONE, StrictJson.UINT64_MAX);
    }

    private static String canonical(JsonNode node) {
        return new String(StrictJson.canonical(node, 81_920), StandardCharsets.UTF_8);
    }

    private static void applyEdit(ObjectNode request, JsonNode edit) {
        JsonNode path = edit.get("path");
        JsonNode parent = request;
        for (int index = 0; index < path.size() - 1; index++) {
            JsonNode key = path.get(index);
            parent = key.isTextual() ? parent.get(key.textValue()) : parent.get(key.intValue());
        }
        JsonNode key = path.get(path.size() - 1);
        if (edit.path("remove").asBoolean()) {
            if (parent instanceof ObjectNode object) object.remove(key.textValue());
            else ((ArrayNode) parent).remove(key.intValue());
        } else {
            JsonNode value = StrictJson.parse(edit.get("value_json").textValue().getBytes(StandardCharsets.UTF_8));
            if (parent instanceof ObjectNode object) object.set(key.textValue(), value);
            else ((ArrayNode) parent).set(key.intValue(), value);
        }
    }
}
