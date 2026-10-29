package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.json.JsonMapper;
import io.quarkus.test.junit.QuarkusTest;
import io.quarkus.test.common.http.TestHTTPResource;
import java.io.InputStream;
import java.net.URI;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.client.G2ClientConfig;
import org.xar.ck3.control.g2.client.G2ClientEvaluationPort;
import org.xar.ck3.control.g2.client.G2ClientException;
import org.xar.ck3.control.g2.client.G2JavaClient;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.wave2.governance.succession.SuccessorUiQueueClient;
import org.xar.ck3.control.wave2.governance.succession.SuccessorUiQueueCodec;

@QuarkusTest
class M3ResidentUiHttpTest {
    private static final ObjectMapper JSON = JsonMapper.builder(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS, DeserializationFeature.USE_BIG_INTEGER_FOR_INTS,
                    DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS).build();
    @TestHTTPResource(G2Wire.HTTP_PATH) URI endpoint;
    private record Golden(byte[] bytes, JsonNode value, G2Source source) {
        private Golden { bytes = bytes.clone(); }
        @Override public byte[] bytes() { return bytes.clone(); }
    }

    @Test void originalRegisteredAppInputsTraverseResidentClientOneHostAndEvidencePersistence() throws Exception {
        Golden golden = golden();
        try (G2JavaClient transport = client()) {
            SuccessorUiQueueClient resident = new SuccessorUiQueueClient(new G2ClientEvaluationPort(transport));
            for (JsonNode row : golden.value().path("cases")) {
                var outcome = resident.consume("m3-resident-" + row.path("name").textValue(), golden.source(), originals(row.path("request")));
                var evaluated = assertInstanceOf(SuccessorUiQueueClient.Evaluated.class, outcome);
                var actual = evaluated.transport().evaluation();
                assertEquals(row.get("expected"), JSON.readTree(SuccessorUiQueueCodec.encode(evaluated.result())));
                assertEquals(golden.source(), actual.response().source());
                assertTrue(actual.evidence().actualHttpInvoked()); assertTrue(actual.evidence().responseComplete());
                assertEquals(200, actual.evidence().httpStatus().orElseThrow());
                var restored = assertInstanceOf(SuccessorUiQueueClient.Evaluated.class,
                        SuccessorUiQueueClient.restore(SuccessorUiQueueClient.persist(evaluated)));
                assertEquals(evaluated.result(), restored.result());
                assertArrayEquals(actual.responseBytes(), restored.transport().evaluation().responseBytes());
                assertEquals(actual.evidence(), restored.transport().evaluation().evidence());
            }
        }
    }

    @Test void originalQueueFailuresReachSharedHostAsDomainRejections() throws Exception {
        Golden golden = golden();
        try (G2JavaClient transport = client()) {
            for (JsonNode row : golden.value().path("rejected")) {
                G2Request request = new G2Request("m3-resident-reject-" + row.path("name").textValue(), Milestone.M3, golden.source(),
                        ProjectionJson.object(JSON.writeValueAsBytes(row.get("request")), ProjectionJson.MAX_BYTES));
                G2ClientException failure = assertThrows(G2ClientException.class, () -> transport.evaluate(request));
                assertEquals(G2ClientException.Reason.HTTP_REJECTED, failure.reason());
                assertEquals(G2HttpError.Code.DOMAIN_REJECTED, failure.httpError().orElseThrow().code());
                assertTrue(failure.evidence().actualHttpInvoked()); assertTrue(failure.evidence().responseComplete());
            }
        }
    }

    @Test void missingResidentProviderIsExplicitUnavailableAndRestoresWithoutAnExchange() throws Exception {
        Golden golden = golden();
        SuccessorUiQueueClient resident = new SuccessorUiQueueClient(G2ClientEvaluationPort.unavailable("resident provider not configured"));
        var unavailable = assertInstanceOf(SuccessorUiQueueClient.Unavailable.class,
                resident.consume("m3-resident-provider-unavailable", golden.source(), originals(golden.value().path("cases").get(0).path("request"))));
        assertTrue(unavailable.transport().failure().isEmpty());
        var restored = assertInstanceOf(SuccessorUiQueueClient.Unavailable.class,
                SuccessorUiQueueClient.restore(SuccessorUiQueueClient.persist(unavailable)));
        assertEquals(unavailable, restored);
    }

    private G2JavaClient client() { return new G2JavaClient(new G2ClientConfig(URI.create("http://127.0.0.1:" + endpoint.getPort()), Duration.ofSeconds(20), G2Wire.MAX_RESPONSE_BYTES)); }
    private static SuccessorUiQueueClient.OriginalInputs originals(JsonNode request) throws Exception {
        return new SuccessorUiQueueClient.OriginalInputs(projection(request.get("transition")), projection(request.get("app_response")), projection(request.get("independent_snapshot")));
    }
    private static ProjectionJson projection(JsonNode value) throws Exception { return ProjectionJson.object(JSON.writeValueAsBytes(value), ProjectionJson.MAX_BYTES); }
    private static Golden golden() throws Exception {
        try (InputStream input = M3ResidentUiHttpTest.class.getResourceAsStream("/g2/m3/original-resident-ui-golden.json")) {
            assertNotNull(input, "original registered-App capture must be mapped; no skip or replacement fixture");
            byte[] bytes = input.readAllBytes(); JsonNode value = JSON.readTree(bytes);
            assertEquals("xar.g2.m3.original-resident-ui-golden/v1", value.path("schema").textValue());
            assertTrue(value.path("source_refs_unchanged").booleanValue()); assertTrue(value.path("synthetic_fixture").booleanValue());
            G2Source source = new G2Source(value.path("machine_id").textValue(), value.path("observed_at_utc").textValue(), "offline-registered-app-fixture",
                    new ExactRef("/g2/m3/original-resident-ui-golden.json", bytes.length, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes))));
            return new Golden(bytes, value, source);
        }
    }
}
