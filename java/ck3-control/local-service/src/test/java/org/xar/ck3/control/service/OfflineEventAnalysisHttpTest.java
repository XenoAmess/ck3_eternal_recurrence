package org.xar.ck3.control.service;

import io.quarkus.test.junit.QuarkusTest;
import io.quarkus.test.common.http.TestHTTPResource;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Duration;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisWire;
import static org.junit.jupiter.api.Assertions.*;

@QuarkusTest
class OfflineEventAnalysisHttpTest {
    @TestHTTPResource("/v1/offline-event-analysis/") URI base;
    private final HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();
    @Test void actualResidentHostPublishesClosedDefaultScopesAndTheTypedProducerIdentity() throws Exception {
        var response = client.send(HttpRequest.newBuilder(base.resolve("context")).GET().build(), HttpResponse.BodyHandlers.ofByteArray());
        assertEquals(200, response.statusCode()); headers(response);
        var context = OfflineEventAnalysisWire.parseMetadataObject(response.body());
        assertEquals(5, context.size()); assertEquals("xar.offline-event-analysis-context/v1", context.path("schema").textValue());
        java.time.Instant.parse(context.path("observed_at_utc").textValue());
        assertTrue(context.get("mandatory_reviews").isNull()); assertTrue(context.get("event_batches").isNull());
    }
    @Test void allThreeActualRoutesKeepUnconfiguredWritersUnavailable() throws Exception {
        var ref = new ExactRef(Path.of("ROOT-ACTUAL-GAME-LAUNCH.json").toAbsolutePath().toString(), 1, "a".repeat(64));
        String[] endpoints = {"mandatory-review-inputs", "mandatory-reviews", "batches"};
        String[] bodies = {
                "{\"schema\":\"xar.offline-mandatory-capture-request/v1\",\"batch_id\":\"http-1\",\"launch_ref\":" + ref.toJson() + "}",
                "{\"schema\":\"xar.offline-mandatory-review-request/v1\",\"batch_id\":\"http-1\",\"source_refs\":[" + ref.toJson() + "]}",
                "{\"schema\":\"xar.offline-event-batch-request/v1\",\"batch_id\":\"http-1\",\"manifest_ref\":" + ref.toJson() + ",\"captured_refs\":[]}"
        };
        for (int index = 0; index < endpoints.length; index++) {
            var response = post(endpoints[index], bodies[index].getBytes(StandardCharsets.UTF_8));
            assertEquals(503, response.statusCode()); headers(response);
            var result = OfflineEventAnalysisWire.parseMetadataObject(response.body());
            assertEquals(5, result.size()); assertEquals("http-1", result.path("batch_id").textValue());
            assertEquals("operation-unavailable", result.path("code").textValue());
        }
    }
    @Test void malformedAndOversizedMetadataAreTypedBeforeAnyProducerDispatch() throws Exception {
        var invalid = post("batches", "{\"schema\":true}".getBytes(StandardCharsets.UTF_8));
        assertEquals(400, invalid.statusCode()); headers(invalid);
        assertEquals("invalid-request", OfflineEventAnalysisWire.parseMetadataObject(invalid.body()).path("code").textValue());
        var oversized = post("mandatory-reviews", new byte[OfflineEventAnalysisContract.MAX_METADATA_BYTES + 1]);
        assertEquals(413, oversized.statusCode()); headers(oversized);
        var error = OfflineEventAnalysisWire.parseMetadataObject(oversized.body());
        assertEquals("xar.offline-event-analysis-error/v1", error.path("schema").textValue());
        assertTrue(error.get("batch_id").isNull()); assertEquals("invalid-request", error.path("code").textValue());
    }
    private HttpResponse<byte[]> post(String endpoint, byte[] body) throws Exception {
        return client.send(HttpRequest.newBuilder(base.resolve(endpoint)).timeout(Duration.ofSeconds(20))
                .header("Content-Type", "application/json").POST(HttpRequest.BodyPublishers.ofByteArray(body)).build(), HttpResponse.BodyHandlers.ofByteArray());
    }
    private static void headers(HttpResponse<byte[]> response) {
        assertEquals(OfflineEventAnalysisResource.PRODUCER, response.headers().firstValue("X-Xar-Producer").orElseThrow());
        assertEquals("0.1.0", response.headers().firstValue("X-Xar-Producer-Version").orElseThrow());
        assertEquals("xar.offline-event-analysis/v1", response.headers().firstValue("X-Xar-Contract-Revision").orElseThrow());
    }
}
