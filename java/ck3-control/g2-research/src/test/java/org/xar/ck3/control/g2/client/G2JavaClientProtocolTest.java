package org.xar.ck3.control.g2.client;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.UnaryOperator;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Exception;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;

import static org.junit.jupiter.api.Assertions.*;

/** Actual loopback HTTP protocol faults only; this fixture is not the Quarkus/domain acceptance host. */
final class G2JavaClientProtocolTest {
    private static final byte[] PAYLOAD = bytes("{\"explicit_null\":null,\"empty\":[],\"decimal\":1.2300,\"negative_zero\":-0.0,\"identity\":\"18446744073709551615\"}");
    private static final G2Source SOURCE = new G2Source("xenoamess-full-tower-eb9d2c1186",
            "2026-10-22T20:00:00Z", "synthetic-protocol-only",
            new ExactRef("D:/synthetic-not-opened/g2-source.json", 3, "0".repeat(64)));

    private static G2Request request(Milestone milestone) {
        return new G2Request("protocol-" + milestone.name(), milestone, SOURCE,
                ProjectionJson.object(PAYLOAD, ProjectionJson.MAX_BYTES));
    }

    @Test void allMilestoneEnvelopesRetainMissingNullEmptyDecimalAndStringIdentity() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client(Duration.ofSeconds(3), G2Wire.MAX_RESPONSE_BYTES)) {
            for (Milestone milestone : Milestone.values()) {
                G2Request input = request(milestone);
                G2Evaluation evaluated = client.evaluateWithEvidence(input);
                assertEquals(input.requestId(), evaluated.response().requestId());
                assertEquals(milestone, evaluated.response().milestone());
                assertEquals(SOURCE, evaluated.response().source());
                assertArrayEquals(PAYLOAD, evaluated.response().result().bytes());
                assertTrue(evaluated.evidence().actualHttpInvoked());
                assertTrue(evaluated.evidence().responseComplete());
                assertEquals(200, evaluated.evidence().httpStatus().orElseThrow());
            }
            assertEquals(Milestone.values().length, fixture.calls.get());
            G2Exception whitespace = assertThrows(G2Exception.class, () -> new G2Request("protocol-whitespace", Milestone.M0, SOURCE,
                    ProjectionJson.object(bytes("  " + new String(PAYLOAD, StandardCharsets.UTF_8) + " \n"), ProjectionJson.MAX_BYTES)));
            assertEquals(G2HttpError.Code.MALFORMED_REQUEST, whitespace.code());
            assertEquals(Milestone.values().length, fixture.calls.get());
        }
    }

    @Test void allCommonTerminalErrorsRetainStatusCodeAndOriginalBytes() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client(Duration.ofSeconds(3), G2Wire.MAX_RESPONSE_BYTES)) {
            for (G2HttpError.Code code : G2HttpError.Code.values()) {
                G2HttpError expected = new G2HttpError(G2HttpError.SCHEMA, code, "synthetic protocol refusal");
                fixture.refusal = expected;
                G2ClientException failure = assertThrows(G2ClientException.class, () -> client.evaluate(request(Milestone.M0)));
                assertEquals(G2ClientException.Reason.HTTP_REJECTED, failure.reason());
                assertEquals(expected, failure.httpError().orElseThrow());
                assertEquals(code.httpStatus(), failure.evidence().httpStatus().orElseThrow());
                assertArrayEquals(G2Wire.encodeError(expected), failure.responseBytes());
                assertTrue(failure.evidence().responseComplete());
                byte[] copy = failure.responseBytes();
                copy[0] = 0;
                assertNotEquals(0, failure.responseBytes()[0]);
            }
            assertEquals(G2HttpError.Code.values().length, fixture.calls.get());
        }
    }

    @Test void explicitNullEmptyAndNumericResultTokensRemainDistinct() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client(Duration.ofSeconds(3), G2Wire.MAX_RESPONSE_BYTES)) {
            for (String token : List.of("null", "[]", "{}", "1.2300", "-0.0", "\"18446744073709551615\"")) {
                fixture.mutation = raw -> raw.replace(new String(PAYLOAD, StandardCharsets.UTF_8), token);
                assertArrayEquals(bytes(token), client.evaluate(request(Milestone.M0)).result().bytes());
            }
            assertEquals(6, fixture.calls.get());
        }
    }

    @Test void wrongMissingExtraDuplicateAndTokenFieldsNeverProduceAResponse() throws Exception {
        List<UnaryOperator<String>> malformed = List.of(
                raw -> raw.replace("\"schema_version\":1", "\"schema_version\":true"),
                raw -> raw.replace("\"schema_version\":1", "\"schema_version\":1.0"),
                raw -> raw.replace("\"schema_version\":1", "\"schema_version\":\"1\""),
                raw -> raw.replace("\"schema_version\":1,", ""),
                raw -> raw.replace("\"schema_version\":1", "\"schema_version\":1,\"extra\":null"),
                raw -> raw.replace("\"schema_version\":1", "\"schema_version\":1,\"schema_version\":1"),
                raw -> raw.replace("\"request_id\":\"protocol-M0\"", "\"request_id\":\"different\""),
                raw -> raw.replace("\"milestone\":\"" + Milestone.M0.wire() + "\"", "\"milestone\":\"" + Milestone.M1.wire() + "\""),
                raw -> raw.replace("\"bytes\":3", "\"bytes\":true"),
                raw -> raw.replace("\"bytes\":3", "\"bytes\":3.0"),
                raw -> raw.replace("\"source\":{", "\"source\":{\"extra\":null,"),
                raw -> raw.replace("\"exact_build\":\"synthetic-protocol-only\"", "\"exact_build\":\"different\""),
                raw -> raw.replace("\"result\":{", "\"missing_result\":{"));
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client(Duration.ofSeconds(3), G2Wire.MAX_RESPONSE_BYTES)) {
            for (UnaryOperator<String> mutation : malformed) {
                fixture.mutation = mutation;
                G2ClientException failure = assertThrows(G2ClientException.class, () -> client.evaluate(request(Milestone.M0)));
                assertEquals(G2ClientException.Reason.RESPONSE_UNVERIFIED, failure.reason());
                assertTrue(failure.httpError().isEmpty());
                assertTrue(failure.evidence().responseComplete());
                assertTrue(failure.evidence().actualHttpInvoked());
            }
            assertEquals(malformed.size(), fixture.calls.get());
        }
    }

    @Test void producerHeadersAndErrorHttpStatusMustMatchTheCommonContract() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client(Duration.ofSeconds(3), G2Wire.MAX_RESPONSE_BYTES)) {
            fixture.producer = "unqualified";
            assertEquals(G2ClientException.Reason.RESPONSE_UNVERIFIED,
                    assertThrows(G2ClientException.class, () -> client.evaluate(request(Milestone.M0))).reason());
            fixture.producer = G2Wire.PRODUCER;
            fixture.duplicateProducer = true;
            assertEquals(G2ClientException.Reason.RESPONSE_UNVERIFIED,
                    assertThrows(G2ClientException.class, () -> client.evaluate(request(Milestone.M0))).reason());
            fixture.duplicateProducer = false;
            fixture.refusal = new G2HttpError(G2HttpError.SCHEMA, G2HttpError.Code.DOMAIN_REJECTED, "wrong status fixture");
            fixture.forceStatus = 500;
            assertEquals(G2ClientException.Reason.RESPONSE_UNVERIFIED,
                    assertThrows(G2ClientException.class, () -> client.evaluate(request(Milestone.M0))).reason());
            assertEquals(3, fixture.calls.get());
        }
    }

    @Test void deadlineAfterHeadersIsTransportUnknownWithoutAutomaticRetry() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client(Duration.ofSeconds(1), G2Wire.MAX_RESPONSE_BYTES)) {
            fixture.stallBody = true;
            long tick = System.nanoTime();
            G2ClientException failure = assertThrows(G2ClientException.class, () -> client.evaluate(request(Milestone.M0)));
            assertEquals(G2ClientException.Reason.TRANSPORT_UNKNOWN, failure.reason());
            assertTrue(fixture.headersSent.await(2, TimeUnit.SECONDS));
            assertTrue(Duration.ofNanos(System.nanoTime() - tick).compareTo(Duration.ofSeconds(4)) < 0);
            assertEquals(200, failure.evidence().httpStatus().orElseThrow());
            assertTrue(failure.evidence().retainedResponseBytes() > 0);
            assertFalse(failure.evidence().responseComplete());
            assertTrue(failure.httpError().isEmpty());
            assertEquals(1, fixture.calls.get());
        }
    }

    @Test void explicitResponseBudgetRetainsOnlyBoundedPrefixWithoutIssuingSuccess() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client(Duration.ofSeconds(3), 64)) {
            G2ClientException failure = assertThrows(G2ClientException.class, () -> client.evaluate(request(Milestone.M0)));
            assertEquals(G2ClientException.Reason.RESPONSE_LIMIT_EXCEEDED, failure.reason());
            assertTrue(failure.evidence().observedResponseBytes() > 64);
            assertEquals(64, failure.responseBytes().length);
            assertFalse(failure.evidence().responseComplete());
            assertEquals(1, fixture.calls.get());
        }
    }

    @Test void nullRequestIsRejectedBeforeAnyHttpInvocation() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client(Duration.ofSeconds(3), G2Wire.MAX_RESPONSE_BYTES)) {
            G2ClientException failure = assertThrows(G2ClientException.class, () -> client.evaluate(null));
            assertEquals(G2ClientException.Reason.LOCAL_REQUEST_INVALID, failure.reason());
            assertFalse(failure.evidence().actualHttpInvoked());
            assertTrue(failure.evidence().httpStatus().isEmpty());
            assertEquals(0, fixture.calls.get());
        }
    }

    @Test void baseUriAndFiniteBudgetsAreRuntimeValidated() {
        for (String value : List.of("https://127.0.0.1:8089", "http://localhost:8089", "http://127.0.0.1",
                "http://127.0.0.1:8089/other", "http://127.0.0.1:8089?mode=1", "http://u@127.0.0.1:8089")) {
            assertThrows(IllegalArgumentException.class, () -> new G2ClientConfig(URI.create(value), Duration.ofSeconds(1), 1));
        }
        assertThrows(IllegalArgumentException.class, () -> new G2ClientConfig(URI.create("http://127.0.0.1:8089"), Duration.ZERO, 1));
        assertThrows(IllegalArgumentException.class, () -> new G2ClientConfig(URI.create("http://127.0.0.1:8089"), Duration.ofSeconds(1), 0));
    }

    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }

    private static final class Fixture implements AutoCloseable {
        private final HttpServer server;
        private final java.util.concurrent.ExecutorService executor = Executors.newCachedThreadPool();
        private final AtomicInteger calls = new AtomicInteger();
        private final CountDownLatch headersSent = new CountDownLatch(1);
        private volatile UnaryOperator<String> mutation = UnaryOperator.identity();
        private volatile G2HttpError refusal;
        private volatile String producer = G2Wire.PRODUCER;
        private volatile boolean duplicateProducer;
        private volatile boolean stallBody;
        private volatile int forceStatus;

        Fixture() throws IOException {
            server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
            server.createContext(G2Wire.HTTP_PATH, this::handle);
            server.setExecutor(executor);
            server.start();
        }

        G2JavaClient client(Duration deadline, int maximumBytes) {
            return new G2JavaClient(new G2ClientConfig(
                    URI.create("http://127.0.0.1:" + server.getAddress().getPort()), deadline, maximumBytes));
        }

        private void handle(HttpExchange exchange) throws IOException {
            calls.incrementAndGet();
            try (exchange) {
                assertEquals("POST", exchange.getRequestMethod());
                G2Request input = G2Wire.decodeRequest(exchange.getRequestBody().readAllBytes());
                G2HttpError error = refusal;
                int status = forceStatus != 0 ? forceStatus : error == null ? 200 : error.code().httpStatus();
                byte[] raw = error == null ? G2Wire.encodeResponse(new G2Response(input.requestId(), input.milestone(), input.source(), input.payload()))
                        : G2Wire.encodeError(error);
                raw = bytes(mutation.apply(new String(raw, StandardCharsets.UTF_8)));
                exchange.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
                exchange.getResponseHeaders().set("X-Xar-Producer", producer);
                if (duplicateProducer) exchange.getResponseHeaders().add("X-Xar-Producer", producer);
                exchange.getResponseHeaders().set("X-Xar-Producer-Version", G2Wire.PRODUCER_VERSION);
                exchange.getResponseHeaders().set("X-Xar-Contract-Revision", G2Wire.REQUEST_SCHEMA);
                exchange.sendResponseHeaders(status, raw.length);
                headersSent.countDown();
                if (stallBody) {
                    exchange.getResponseBody().write(raw, 0, 1);
                    exchange.getResponseBody().flush();
                    try {
                        Thread.sleep(2000);
                    } catch (InterruptedException interrupted) {
                        Thread.currentThread().interrupt();
                        return;
                    }
                }
                try {
                    exchange.getResponseBody().write(raw, stallBody ? 1 : 0, raw.length - (stallBody ? 1 : 0));
                } catch (IOException cancelled) {
                    if (!stallBody) throw cancelled;
                }
            }
        }

        @Override public void close() {
            server.stop(0);
            executor.shutdownNow();
        }
    }
}
