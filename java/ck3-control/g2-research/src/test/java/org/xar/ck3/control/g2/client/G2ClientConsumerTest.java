package org.xar.ck3.control.g2.client;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.UnaryOperator;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;

import static org.junit.jupiter.api.Assertions.*;

/** Real protocol HTTP consumer tests; this fault fixture grants no Quarkus/domain qualification. */
final class G2ClientConsumerTest {
    private static final G2Source SOURCE = new G2Source("xenoamess-full-tower-eb9d2c1186",
            "2026-10-23T00:00:00Z", "consumer-protocol-fixture-only",
            new ExactRef("D:/synthetic-not-opened/consumer-source.json", 4, "1".repeat(64)));
    private static final byte[] PAYLOAD = bytes("{\"null\":null,\"empty\":[],\"number\":1.2300,\"zero\":-0.0,\"identity\":\"18446744073709551615\"}");

    @Test void actualConsumerRetainsOriginalEnvelopeAndLexicalDomainPayloadAcrossPersistence() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client()) {
            G2ClientEvaluationPort port = new G2ClientEvaluationPort(client);
            for (Milestone milestone : Milestone.values()) {
                G2ClientOutcome.Success success = assertInstanceOf(G2ClientOutcome.Success.class, port.evaluate(request(milestone, PAYLOAD)));
                assertArrayEquals(fixture.lastResponse, success.evaluation().responseBytes());
                assertArrayEquals(PAYLOAD, success.evaluation().response().result().bytes());
                assertEquals(SOURCE, success.evaluation().response().source());
                G2ClientOutcome.Success restored = assertInstanceOf(G2ClientOutcome.Success.class,
                        G2ClientOutcomeWire.decode(G2ClientOutcomeWire.encode(success)));
                assertArrayEquals(fixture.lastResponse, restored.evaluation().responseBytes());
                assertArrayEquals(PAYLOAD, restored.evaluation().response().result().bytes());
                assertEquals(success.evaluation().evidence(), restored.evaluation().evidence());
                assertFalse(java.util.Arrays.equals(fixture.lastResponse, G2Wire.encodeResponse(restored.evaluation().response())));
                byte[] copy = restored.evaluation().responseBytes();
                copy[0] = 0;
                assertNotEquals(0, restored.evaluation().responseBytes()[0]);
            }
            assertEquals(8, fixture.calls.get());
            byte[] large = bytes("{\"opaque\":\"" + "x".repeat(50_000) + "\"}");
            G2ClientOutcome.Success success = assertInstanceOf(G2ClientOutcome.Success.class, port.evaluate(request(Milestone.M3, large)));
            G2ClientOutcome.Success restored = assertInstanceOf(G2ClientOutcome.Success.class,
                    G2ClientOutcomeWire.decode(G2ClientOutcomeWire.encode(success)));
            assertArrayEquals(large, restored.evaluation().response().result().bytes());
            assertEquals(9, fixture.calls.get());
        }
    }

    @Test void unavailableAndEveryOtherVerifiedTerminalRemainDifferentTypedBranches() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client()) {
            G2ClientEvaluationPort port = new G2ClientEvaluationPort(client);
            for (G2HttpError.Code code : G2HttpError.Code.values()) {
                fixture.error = new G2HttpError(G2HttpError.SCHEMA, code, "original HTTP refusal " + code);
                G2ClientOutcome result = port.evaluate(request(Milestone.M3, PAYLOAD));
                G2ClientException failure;
                if (code == G2HttpError.Code.ENGINE_UNAVAILABLE) {
                    G2ClientOutcome.Unavailable unavailable = assertInstanceOf(G2ClientOutcome.Unavailable.class, result);
                    assertEquals(G2ClientOutcome.UnavailableReason.ENGINE_UNAVAILABLE, unavailable.reason());
                    failure = unavailable.failure().orElseThrow();
                } else failure = assertInstanceOf(G2ClientOutcome.Failed.class, result).failure();
                G2ClientOutcome restored = G2ClientOutcomeWire.decode(G2ClientOutcomeWire.encode(result));
                G2ClientException recovered = restored instanceof G2ClientOutcome.Unavailable unavailable
                        ? unavailable.failure().orElseThrow() : assertInstanceOf(G2ClientOutcome.Failed.class, restored).failure();
                assertEquals(G2ClientException.Reason.HTTP_REJECTED, recovered.reason());
                assertEquals(code, recovered.httpError().orElseThrow().code());
                assertEquals(failure.evidence(), recovered.evidence());
                assertArrayEquals(fixture.lastResponse, recovered.responseBytes());
            }
            assertEquals(7, fixture.calls.get());
        }
    }

    @Test void absentProviderDoesNotConstructOrInvokeHttpAndHasNoInventedEvidence() {
        G2ClientOutcome.Unavailable result = assertInstanceOf(G2ClientOutcome.Unavailable.class,
                G2ClientEvaluationPort.unavailable("Original Root provider is not installed").evaluate(null));
        assertEquals(G2ClientOutcome.UnavailableReason.PROVIDER_NOT_CONFIGURED, result.reason());
        assertTrue(result.failure().isEmpty());
        assertEquals(result, G2ClientOutcomeWire.decode(G2ClientOutcomeWire.encode(result)));
        assertThrows(IllegalArgumentException.class, () -> G2ClientEvaluationPort.unavailable(" "));
    }

    @Test void localInvalidAndResponseSourceMismatchKeepFailureAndOriginalBytes() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client()) {
            G2ClientEvaluationPort port = new G2ClientEvaluationPort(client);
            G2ClientOutcome.Failed invalid = assertInstanceOf(G2ClientOutcome.Failed.class, port.evaluate(null));
            assertEquals(G2ClientException.Reason.LOCAL_REQUEST_INVALID, invalid.failure().reason());
            assertFalse(invalid.failure().evidence().actualHttpInvoked());
            assertEquals(0, fixture.calls.get());
            G2ClientOutcome.Failed localRestored = assertInstanceOf(G2ClientOutcome.Failed.class,
                    G2ClientOutcomeWire.decode(G2ClientOutcomeWire.encode(invalid)));
            assertFalse(localRestored.failure().evidence().actualHttpInvoked());
            G2ClientException expired = assertThrows(G2ClientException.class,
                    () -> client.evaluateWithEvidence(request(Milestone.M3, PAYLOAD), Duration.ofNanos(1)));
            assertEquals(G2ClientException.Reason.LOCAL_DEADLINE_EXPIRED, expired.reason());
            G2ClientOutcome.Failed expiredRestored = assertInstanceOf(G2ClientOutcome.Failed.class,
                    G2ClientOutcomeWire.decode(G2ClientOutcomeWire.encode(new G2ClientOutcome.Failed(expired))));
            assertEquals(G2ClientException.Reason.LOCAL_DEADLINE_EXPIRED, expiredRestored.failure().reason());
            assertFalse(expiredRestored.failure().evidence().actualHttpInvoked());
            assertEquals(0, fixture.calls.get());
            fixture.mutation = raw -> raw.replace("consumer-protocol-fixture-only", "unbound-build");
            G2ClientOutcome.Failed mismatch = assertInstanceOf(G2ClientOutcome.Failed.class, port.evaluate(request(Milestone.M3, PAYLOAD)));
            assertEquals(G2ClientException.Reason.RESPONSE_UNVERIFIED, mismatch.failure().reason());
            G2ClientOutcome.Failed restored = assertInstanceOf(G2ClientOutcome.Failed.class,
                    G2ClientOutcomeWire.decode(G2ClientOutcomeWire.encode(mismatch)));
            assertArrayEquals(fixture.lastResponse, restored.failure().responseBytes());
            assertTrue(restored.failure().httpError().isEmpty());
            assertEquals(1, fixture.calls.get());
        }
    }

    @Test void persistedWrongMissingDuplicateAndNumericTypesAreRejected() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client()) {
            G2ClientOutcome success = new G2ClientEvaluationPort(client).evaluate(request(Milestone.M3, PAYLOAD));
            String original = new String(G2ClientOutcomeWire.encode(success), StandardCharsets.UTF_8);
            List<UnaryOperator<String>> corruptions = List.of(
                    raw -> raw.replace("\"status\":\"SUCCESS\"", "\"status\":\"FAILED\""),
                    raw -> raw.replace("\"schema\":", "\"extra\":null,\"schema\":"),
                    raw -> raw.replace("\"schema\":", "\"status\":\"SUCCESS\",\"schema\":"),
                    raw -> raw.replace("\"response_complete\":true", "\"response_complete\":1"),
                    raw -> raw.replace("\"actual_http_invoked\":true", "\"actual_http_invoked\":null"),
                    raw -> raw.replace("\"http_status\":200", "\"http_status\":200.0"),
                    raw -> raw.replace("\"http_status\":200", "\"http_status\":true"),
                    raw -> raw.replace("\"response_bytes_base64\":\"", "\"response_bytes_base64\":\"A"),
                    raw -> raw.replace("\"request_bytes\":\"", "\"request_bytes\":\"0"),
                    raw -> raw.replace("\"retained_response_sha256\":\"", "\"retained_response_sha256\":\"0"),
                    raw -> raw.replace("\"evidence\":{", "\"evidence\":{\"unknown\":false,"));
            for (UnaryOperator<String> corruption : corruptions) {
                assertThrows(RuntimeException.class, () -> G2ClientOutcomeWire.decode(bytes(corruption.apply(original))));
            }
            assertThrows(RuntimeException.class, () -> G2ClientOutcomeWire.decode(bytes(original + "null")));
            assertThrows(RuntimeException.class, () -> G2ClientOutcomeWire.decode(new byte[] {(byte) 0xc3, 0x28}));
            assertThrows(RuntimeException.class, () -> G2ClientOutcomeWire.decode(bytes("null")));
            assertEquals(1, fixture.calls.get());
        }
    }

    @Test void limitedOriginalPrefixRemainsFailureAcrossPersistenceWithoutRetry() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = new G2JavaClient(new G2ClientConfig(
                fixture.baseUri(), Duration.ofSeconds(3), 64))) {
            G2ClientOutcome.Failed failed = assertInstanceOf(G2ClientOutcome.Failed.class,
                    new G2ClientEvaluationPort(client).evaluate(request(Milestone.M3, PAYLOAD)));
            assertEquals(G2ClientException.Reason.RESPONSE_LIMIT_EXCEEDED, failed.failure().reason());
            G2ClientOutcome.Failed restored = assertInstanceOf(G2ClientOutcome.Failed.class,
                    G2ClientOutcomeWire.decode(G2ClientOutcomeWire.encode(failed)));
            assertArrayEquals(failed.failure().responseBytes(), restored.failure().responseBytes());
            assertEquals(64, restored.failure().responseBytes().length);
            assertFalse(restored.failure().evidence().responseComplete());
            assertEquals(1, fixture.calls.get());
        }
    }

    private static G2Request request(Milestone milestone, byte[] payload) {
        return new G2Request("consumer-" + milestone.name(), milestone, SOURCE,
                ProjectionJson.object(payload, ProjectionJson.MAX_BYTES));
    }
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }

    private static final class Fixture implements AutoCloseable {
        private final HttpServer server;
        private final java.util.concurrent.ExecutorService executor = Executors.newCachedThreadPool();
        private final AtomicInteger calls = new AtomicInteger();
        private volatile G2HttpError error;
        private volatile UnaryOperator<String> mutation = UnaryOperator.identity();
        private volatile byte[] lastResponse = new byte[0];

        Fixture() throws IOException {
            server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
            server.createContext(G2Wire.HTTP_PATH, this::handle);
            server.setExecutor(executor);
            server.start();
        }
        URI baseUri() { return URI.create("http://127.0.0.1:" + server.getAddress().getPort()); }
        G2JavaClient client() { return new G2JavaClient(new G2ClientConfig(baseUri(), Duration.ofSeconds(3), G2Wire.MAX_RESPONSE_BYTES)); }

        private void handle(HttpExchange exchange) throws IOException {
            calls.incrementAndGet();
            try (exchange) {
                G2Request input = G2Wire.decodeRequest(exchange.getRequestBody().readAllBytes());
                G2HttpError refusal = error;
                byte[] compact = refusal == null ? G2Wire.encodeResponse(new G2Response(input.requestId(), input.milestone(), input.source(), input.payload()))
                        : G2Wire.encodeError(refusal);
                byte[] raw = bytes(mutation.apply("{ \n" + new String(compact, StandardCharsets.UTF_8).substring(1)));
                lastResponse = raw;
                exchange.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
                exchange.getResponseHeaders().set("X-Xar-Producer", G2Wire.PRODUCER);
                exchange.getResponseHeaders().set("X-Xar-Producer-Version", G2Wire.PRODUCER_VERSION);
                exchange.getResponseHeaders().set("X-Xar-Contract-Revision", G2Wire.REQUEST_SCHEMA);
                exchange.sendResponseHeaders(refusal == null ? 200 : refusal.code().httpStatus(), raw.length);
                exchange.getResponseBody().write(raw);
            }
        }
        @Override public void close() { server.stop(0); executor.shutdownNow(); }
    }
}
