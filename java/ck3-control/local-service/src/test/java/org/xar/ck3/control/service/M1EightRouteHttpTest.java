package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusTest;
import jakarta.inject.Inject;
import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.security.MessageDigest;
import java.time.Duration;
import java.util.HexFormat;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.client.G2ClientConfig;
import org.xar.ck3.control.g2.client.G2JavaClient;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.m1.M1Operation;
import org.xar.ck3.control.g2.m1.M1ResultConsumers;

/** All M1 operations use the existing Quarkus host, exact shared transport, typed consumer and disk wire. */
@QuarkusTest
class M1EightRouteHttpTest {
    @TestHTTPResource(G2Wire.HTTP_PATH) URI endpoint;
    @Inject G2ResearchHost host;
    @TempDir Path persistence;

    @ParameterizedTest @EnumSource(M1Operation.class)
    void everyExportedOperationReachesTheSameHostClientConsumerAndPersistence(M1Operation operation) throws Exception {
        JsonNode index = StrictJson.parse(resource("M1.fixture-index.json"), M1ResultConsumers.MAX_BYTES);
        JsonNode entry = operationEntry(index, operation);
        byte[] raw = checkedFixture("M1." + operation.wire() + ".request.json", entry.get("request"));
        byte[] expected = checkedFixture("M1." + operation.wire() + ".expected-result.json", entry.get("expected_result"));
        G2Request request = G2Wire.decodeRequest(raw);
        assertEquals(operation.wire(), StrictJson.parse(request.payload().bytes(), M1ResultConsumers.MAX_BYTES).path("operation").textValue());
        assertTrue(request.source().exactBuild().startsWith("pure-producer:"), "fixture source must not claim current Native build authority");
        G2Response direct = host.evaluate(request);
        assertArrayEquals(expected, direct.result().bytes());
        HttpResponse<byte[]> actual = HttpClient.newHttpClient().send(
                HttpRequest.newBuilder(baseUri().resolve(G2Wire.HTTP_PATH)).timeout(Duration.ofSeconds(20)).header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofByteArray(raw)).build(), HttpResponse.BodyHandlers.ofByteArray());
        assertEquals(200, actual.statusCode());
        assertEquals(G2Wire.PRODUCER, actual.headers().firstValue("X-Xar-Producer").orElseThrow());
        assertEquals(G2Wire.PRODUCER_VERSION, actual.headers().firstValue("X-Xar-Producer-Version").orElseThrow());
        assertEquals(G2Wire.REQUEST_SCHEMA, actual.headers().firstValue("X-Xar-Contract-Revision").orElseThrow());
        assertArrayEquals(G2Wire.encodeResponse(direct), actual.body());
        try (G2JavaClient client = new G2JavaClient(new G2ClientConfig(
                baseUri(), Duration.ofSeconds(20), G2Wire.MAX_RESPONSE_BYTES))) {
            G2Response response = client.evaluate(request);
            assertArrayEquals(expected, response.result().bytes());
            assertEquals(request.source(), response.source()); assertEquals(request.requestId(), response.requestId());
            Path saved = persistence.resolve(operation.wire() + ".response.json");
            Files.write(saved, G2Wire.encodeResponse(response), StandardOpenOption.CREATE_NEW);
            G2Response restored = G2Wire.decodeResponse(Files.readAllBytes(saved));
            assertArrayEquals(response.result().bytes(), restored.result().bytes());
            assertEquals(response.source(), restored.source());
            consume(operation, restored.result().bytes());
        }
    }

    @Test void exportedUnknownOperationRetainsTypedHttpRejection() throws Exception {
        byte[] raw = resource("M1.rejected-request.json");
        HttpResponse<byte[]> result = HttpClient.newHttpClient().send(
                HttpRequest.newBuilder(baseUri().resolve(G2Wire.HTTP_PATH)).timeout(Duration.ofSeconds(20)).header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofByteArray(raw)).build(), HttpResponse.BodyHandlers.ofByteArray());
        assertEquals(422, result.statusCode());
        assertArrayEquals(resource("M1.expected-http-error.json"), result.body());
        assertEquals(G2HttpError.Code.DOMAIN_REJECTED, G2Wire.decodeError(result.body()).code());
    }

    private URI baseUri() { return URI.create("http://127.0.0.1:" + endpoint.getPort()); }

    private static void consume(M1Operation operation, byte[] raw) {
        switch (operation) {
            case SAVED_MEMBERSHIP -> assertTrue(M1ResultConsumers.savedMembership(raw).realm().complete());
            case REALM_FEEDBACK -> assertInstanceOf(M1ResultConsumers.AvailableFeedback.class, M1ResultConsumers.realmFeedback(raw));
            case MONTHLY_OBSERVATION -> assertTrue(M1ResultConsumers.monthlyObservation(raw).isPresent());
            case NATIVE_DIFFERENCE -> assertInstanceOf(org.xar.ck3.control.wave2.planning.realmcompare.RealmDifference.Unavailable.class,
                    M1ResultConsumers.nativeDifference(raw));
            case NATIVE_CACHE, MONTHLY_CACHE -> assertEquals(org.xar.ck3.control.g2.m1.M1RealmComparisons.CacheStatus.CURRENT,
                    M1ResultConsumers.cache(raw));
            case SAVED_DIFFERENCE -> assertInstanceOf(org.xar.ck3.control.g2.m1.M1RealmComparisons.SavedUnavailable.class,
                    M1ResultConsumers.savedDifference(raw));
            case DATED_SUMMARY -> assertInstanceOf(M1ResultConsumers.RetainedSummary.class, M1ResultConsumers.datedSummary(raw));
        }
    }
    private static JsonNode operationEntry(JsonNode index, M1Operation operation) throws IOException {
        assertEquals(8, index.path("operations").size(), "complete actual exporter output required");
        for (JsonNode entry : index.path("operations")) {
            if (operation.wire().equals(entry.path("operation").textValue())) { return entry; }
        }
        throw new IOException("required actual exported M1 operation missing: " + operation.wire());
    }
    private static byte[] checkedFixture(String name, JsonNode reference) throws Exception {
        byte[] raw = resource(name); assertEquals(reference.path("bytes").longValue(), raw.length);
        assertEquals(reference.path("sha256").textValue(), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)));
        return raw;
    }
    private static byte[] resource(String name) throws IOException {
        try (InputStream input = M1EightRouteHttpTest.class.getResourceAsStream("/g2-http/" + name)) {
            if (input == null) { throw new IOException("actual M1 exporter fixture missing: " + name); }
            byte[] raw = input.readNBytes(G2Wire.MAX_REQUEST_BYTES + 1);
            if (raw.length == 0 || raw.length > G2Wire.MAX_REQUEST_BYTES) { throw new IOException("finite M1 fixture required"); }
            return raw;
        }
    }
}
