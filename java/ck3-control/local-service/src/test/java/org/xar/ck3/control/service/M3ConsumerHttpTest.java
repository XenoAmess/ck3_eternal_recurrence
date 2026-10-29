package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.json.JsonMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusTest;
import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.time.Duration;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.client.G2ClientConfig;
import org.xar.ck3.control.g2.client.G2ClientException;
import org.xar.ck3.control.g2.client.G2JavaClient;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;

/** Actual Quarkus/shared-client transport over captured original M3 readers; no domain logic in host tests. */
@QuarkusTest
class M3ConsumerHttpTest {
    private static final ObjectMapper JSON = JsonMapper.builder(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS, DeserializationFeature.USE_BIG_INTEGER_FOR_INTS,
                    DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .disable(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES).build();
    @TestHTTPResource(G2Wire.HTTP_PATH) URI endpoint;

    private record Golden(String name, JsonNode document, byte[] bytes) {
        private Golden { bytes = bytes.clone(); }
        @Override public byte[] bytes() { return bytes.clone(); }
    }

    @Test
    void capturedOriginalReadersAndFreshRootDecisionsTraverseSharedClientAndRealHost() throws Exception {
        try (G2JavaClient client = client()) {
            for (String name : List.of("original-producer-golden.json", "original-retained-consumer-golden.json")) {
                Golden golden = golden(name); String group = name.equals("original-producer-golden.json") ? "consumer_cases" : "cases";
                JsonNode cases = golden.document().path(group);
                assertTrue(cases.isArray() && !cases.isEmpty(), "actual original reader cases required");
                for (JsonNode row : cases) {
                    G2Request request = request(golden, row.path("name").textValue(), row.get("request"));
                    var evaluated = client.evaluateWithEvidence(request);
                    G2Response response = evaluated.response();
                    assertEquals(row.get("expected"), JSON.readTree(response.result().bytes()), row.path("name").textValue());
                    assertIdentity(request, response);
                    assertTrue(evaluated.evidence().actualHttpInvoked());
                    assertTrue(evaluated.evidence().responseComplete());
                    assertEquals(200, evaluated.evidence().httpStatus().orElseThrow());
                    JsonNode persisted = JSON.readTree(G2Wire.decodeResponse(G2Wire.encodeResponse(response)).result().bytes());
                    assertEquals(row.get("expected"), persisted, "JSON save/restore retains nulls, empty arrays, integers and full title metadata");
                    if (!persisted.isNull() && (row.path("request").path("operation").textValue().equals("invalidate")
                            || row.path("request").path("operation").textValue().equals("warm_refresh"))) {
                        assertFalse(persisted.path("submission_authorized").booleanValue());
                        assertEquals(0, persisted.path("queries_performed").intValue());
                    }
                }
                if (name.equals("original-producer-golden.json")) {
                    for (String producerGroup : List.of("producer_cases", "freshness_cases")) {
                        for (JsonNode row : golden.document().path(producerGroup)) {
                            assertHttpResult(client, golden, "original-" + row.path("name").textValue(), row.get("request"), row.get("expected"));
                            if (producerGroup.equals("producer_cases")) {
                                assertHttpResult(client, golden, "pure-" + row.path("name").textValue(), legacyRequest(row.get("request")), row.get("expected"));
                                if ("retain".equals(row.path("request").path("operation").textValue())) {
                                    ObjectNode normalize = JSON.createObjectNode();
                                    normalize.put("schema", "xar.java-succession-request/v1").put("operation", "normalize");
                                    normalize.set("expectation", row.get("expected"));
                                    assertHttpResult(client, golden, "normalize-" + row.path("name").textValue(), normalize, row.get("expected"));
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    @Test
    void actualHttpProducerOutputReentersAllFourRetainedConsumers() throws Exception {
        Golden golden = golden("original-producer-golden.json");
        JsonNode seed = null;
        for (JsonNode row : golden.document().path("consumer_cases")) {
            if ("restore_complete".equals(row.path("name").textValue())) { seed = row.path("request").get("expectation"); }
        }
        assertNotNull(seed, "original complete restore seed is required");
        try (G2JavaClient client = client()) {
            JsonNode produced = null;
            for (JsonNode row : golden.document().path("producer_cases")) {
                if ("retain".equals(row.path("request").path("operation").textValue()) && seed.equals(row.get("expected"))) {
                    G2Request producing = request(golden, "linked-producer", row.get("request"));
                    var result = client.evaluateWithEvidence(producing);
                    assertIdentity(producing, result.response());
                    assertTrue(result.evidence().actualHttpInvoked()); assertTrue(result.evidence().responseComplete());
                    produced = JSON.readTree(result.response().result().bytes());
                    assertEquals(row.get("expected"), produced, "actual HTTP producer equals the complete original seed");
                    break;
                }
            }
            assertNotNull(produced, "actual original producer matching the reader seed is required");
            int linked = 0;
            for (JsonNode row : golden.document().path("consumer_cases")) {
                if (!List.of("restore_complete", "retained_reader_complete", "wal_complete_business", "saved_basis_complete")
                        .contains(row.path("name").textValue())) { continue; }
                ObjectNode incoming = object(row.get("request")).deepCopy();
                switch (incoming.path("operation").textValue()) {
                    case "restore", "retained_reader" -> incoming.set("expectation", produced.deepCopy());
                    case "wal_business" -> object(incoming.get("fields")).set("succession_expectation", produced.deepCopy());
                    case "saved_basis_flags" -> object(incoming.get("flags")).set("succession_expectation", produced.deepCopy());
                    default -> throw new IllegalArgumentException("unexpected retained reader operation");
                }
                JsonNode persistedInput = JSON.readTree(JSON.writeValueAsBytes(incoming));
                assertHttpResult(client, golden, "linked-" + row.path("name").textValue(), persistedInput, row.get("expected"));
                linked++;
            }
            assertEquals(4, linked, "all four original readers consume the actual HTTP producer result after serialization");
        }
    }

    private static ObjectNode object(JsonNode value) {
        if (value instanceof ObjectNode object) { return object; }
        throw new IllegalArgumentException("original reader request object required");
    }

    private static void assertHttpResult(G2JavaClient client, Golden golden, String id, JsonNode payload, JsonNode expected) throws Exception {
        G2Request request = request(golden, id, payload);
        var evaluated = client.evaluateWithEvidence(request);
        assertIdentity(request, evaluated.response());
        assertTrue(evaluated.evidence().actualHttpInvoked()); assertTrue(evaluated.evidence().responseComplete());
        assertEquals(expected, JSON.readTree(evaluated.response().result().bytes()));
    }

    private static ObjectNode legacyRequest(JsonNode producer) {
        ObjectNode request = JSON.createObjectNode(); request.put("schema", "xar.java-succession-request/v1");
        if ("retain".equals(producer.path("operation").textValue())) {
            request.put("operation", "freeze"); request.set("turn_bundle", producer.get("turn_bundle"));
            request.set("episode_run_id", producer.path("snapshot").get("episode_run_id"));
            request.set("episode_character_id", producer.path("snapshot").get("episode_character_id"));
        } else {
            request.put("operation", "reconcile"); request.set("expectation", producer.get("expectation"));
            request.set("post_snapshot", producer.get("snapshot")); request.set("post_turn_bundle", producer.get("turn_bundle"));
        }
        return request;
    }

    @Test
    void savedFlagsReenterTheOriginalConsumerAfterTheActualHttpResponseWasSerialized() throws Exception {
        Golden golden = golden("original-producer-golden.json");
        try (G2JavaClient client = client()) {
            for (JsonNode row : golden.document().path("consumer_cases")) {
                if (!"saved_basis_flags".equals(row.path("request").path("operation").textValue())) { continue; }
                G2Response first = client.evaluate(request(golden, "saved-first-" + row.path("name").textValue(), row.get("request")));
                G2Response restored = G2Wire.decodeResponse(G2Wire.encodeResponse(first));
                ObjectNode again = JSON.createObjectNode();
                again.put("schema", "xar.java-succession-retained-consumer/v1").put("operation", "saved_basis_flags");
                again.set("flags", JSON.readTree(restored.result().bytes()));
                G2Request second = request(golden, "saved-second-" + row.path("name").textValue(), again);
                G2Response roundtrip = client.evaluate(second);
                assertIdentity(second, roundtrip);
                assertEquals(row.get("expected"), JSON.readTree(roundtrip.result().bytes()));
            }
        }
    }

    @Test
    void originalRejectedReaderInputsAreVerifiedDomainRejectionsAtTheActualEndpoint() throws Exception {
        try (G2JavaClient client = client()) {
            for (String name : List.of("original-producer-golden.json", "original-retained-consumer-golden.json")) {
                Golden golden = golden(name); String group = name.equals("original-producer-golden.json") ? "consumer_rejected" : "rejected";
                JsonNode cases = golden.document().path(group);
                assertTrue(cases.isArray() && !cases.isEmpty(), "actual original failures cannot become an empty green seam");
                for (JsonNode row : cases) {
                    assertTrue(row.path("error_type").isTextual());
                    G2Request request = request(golden, "reject-" + row.path("name").textValue(), row.get("request"));
                    G2ClientException rejected = assertThrows(G2ClientException.class, () -> client.evaluate(request));
                    assertEquals(G2ClientException.Reason.HTTP_REJECTED, rejected.reason());
                    assertEquals(G2HttpError.Code.DOMAIN_REJECTED, rejected.httpError().orElseThrow().code());
                    assertTrue(rejected.evidence().actualHttpInvoked());
                    assertTrue(rejected.evidence().responseComplete());
                    assertEquals(G2HttpError.Code.DOMAIN_REJECTED.httpStatus(), rejected.evidence().httpStatus().orElseThrow());
                }
            }
        }
    }

    private G2JavaClient client() {
        return new G2JavaClient(new G2ClientConfig(URI.create("http://127.0.0.1:" + endpoint.getPort()),
                Duration.ofSeconds(20), G2Wire.MAX_RESPONSE_BYTES));
    }
    private static G2Request request(Golden golden, String id, JsonNode payload) throws Exception {
        byte[] original = golden.bytes();
        G2Source source = new G2Source(golden.document().path("machine_id").textValue(),
                golden.document().path("observed_at_utc").textValue(), "offline-original-producer-fixture",
                new ExactRef("/g2/m3/" + golden.name(), original.length,
                        HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(original))));
        return new G2Request("m3-http-" + id, Milestone.M3, source,
                ProjectionJson.object(JSON.writeValueAsBytes(payload), ProjectionJson.MAX_BYTES));
    }
    private static void assertIdentity(G2Request request, G2Response response) {
        assertEquals(request.requestId(), response.requestId()); assertEquals(Milestone.M3, response.milestone());
        assertEquals(request.source(), response.source(), "source echo is provenance only and grants no action authority");
    }
    private static Golden golden(String name) throws IOException {
        try (InputStream input = M3ConsumerHttpTest.class.getResourceAsStream("/g2/m3/" + name)) {
            assertNotNull(input, "original producer resource must be mapped from g2-research test resources; no default Python or skip");
            byte[] bytes = input.readAllBytes(); JsonNode document = JSON.readTree(bytes);
            assertTrue(document.path("synthetic_fixture").booleanValue());
            assertTrue(document.path("source_refs_unchanged").booleanValue());
            return new Golden(name, document, bytes);
        }
    }
}
