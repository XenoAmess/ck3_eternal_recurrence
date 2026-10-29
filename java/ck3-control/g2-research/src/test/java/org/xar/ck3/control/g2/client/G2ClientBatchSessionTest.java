package org.xar.ck3.control.g2.client;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
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

/** Actual loopback protocol/consumer tests. This fixture neither launches Quarkus nor invokes Game. */
final class G2ClientBatchSessionTest {
    private static final G2Source SOURCE = new G2Source("xenoamess-full-tower-eb9d2c1186", "2026-10-22T23:00:00Z",
            "synthetic-batch-protocol", new ExactRef("D:/synthetic-not-opened/batch.json", 3, "0".repeat(64)));
    private static final G2ClientBatchSession.Budget BUDGET = new G2ClientBatchSession.Budget(16, Duration.ofSeconds(10));
    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
    private static G2Request request(int index) {
        String strategy = index % 2 == 0 ? "ordinary" : "war";
        return new G2Request("batch-" + index, Milestone.values()[index % Milestone.values().length], SOURCE,
                ProjectionJson.object(bytes("{\"strategy\":\"" + strategy + "\",\"null\":null,\"empty\":[],\"decimal\":1.2300,\"negative_zero\":-0.0,\"id\":\"18446744073709551615\"}"), ProjectionJson.MAX_BYTES));
    }

    @Test void retainedSessionMatchesSequentialOriginalWireAcrossAllMilestonesAndReusesConnection() throws Exception {
        int count = Milestone.values().length;
        List<byte[]> baseline = new ArrayList<>();
        try (Fixture fixture = new Fixture()) {
            for (int index = 0; index < count; index++) {
                try (G2JavaClient client = fixture.client()) { baseline.add(client.evaluateWithEvidence(request(index)).responseBytes()); }
            }
            assertEquals(count, fixture.remotePorts.size());
        }
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client()) {
            AtomicInteger produced = new AtomicInteger(), consumed = new AtomicInteger();
            List<byte[]> actual = new ArrayList<>();
            G2ClientBatchSession session = new G2ClientBatchSession(client, SOURCE.machineId());
            G2ClientBatchSession.Result result = session.run(BUDGET, preceding -> {
                int index = produced.getAndIncrement();
                assertEquals(index, consumed.get(), "next producer waits for preceding consumer");
                if (index == 0) assertTrue(preceding.isEmpty());
                else assertEquals("batch-" + (index - 1), preceding.orElseThrow().response().requestId());
                return index == count ? G2ClientBatchSession.Complete.INSTANCE : new G2ClientBatchSession.Evaluate(request(index));
            }, evaluated -> { actual.add(evaluated.responseBytes()); consumed.incrementAndGet(); });
            assertEquals(G2ClientBatchSession.Stop.COMPLETE, result.summary().stop());
            assertEquals(count, result.summary().consumedResponses());
            assertEquals(1, fixture.remotePorts.size(), "one actual retained HTTP connection");
            assertEquals(count, fixture.requests.size());
            for (int index = 0; index < count; index++) {
                assertArrayEquals(baseline.get(index), actual.get(index));
                assertArrayEquals(G2Wire.encodeRequest(request(index)), fixture.requests.get(index));
            }
            assertEquals(result.summary(), G2ClientBatchWire.decode(G2ClientBatchWire.encode(result.summary())));
            assertTrue(result.failure().isEmpty());
            // A new finite batch uses the same client/host, without restarting either.
            assertEquals(G2ClientBatchSession.Stop.COMPLETE,
                    session.run(BUDGET, previous -> G2ClientBatchSession.Complete.INSTANCE, evaluated -> fail()).summary().stop());
        }
    }

    @Test void verifiedHttpRefusalStopsBeforeDependentProducerAndRetainsActualFailure() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client()) {
            fixture.rejectAt = 2;
            AtomicInteger produced = new AtomicInteger(), consumed = new AtomicInteger();
            var result = new G2ClientBatchSession(client, SOURCE.machineId()).run(BUDGET,
                    preceding -> new G2ClientBatchSession.Evaluate(request(produced.getAndIncrement())),
                    evaluated -> consumed.incrementAndGet());
            assertEquals(G2ClientBatchSession.Stop.CLIENT_FAILED, result.summary().stop());
            assertEquals(Optional.of(G2ClientException.Reason.HTTP_REJECTED), result.summary().clientFailureReason());
            assertEquals(2, produced.get()); assertEquals(2, fixture.calls.get()); assertEquals(1, consumed.get());
            assertEquals(2, result.summary().submittedRequests()); assertEquals(1, result.summary().verifiedResponses());
            G2ClientException failure = assertInstanceOf(G2ClientException.class, result.failure().orElseThrow());
            assertEquals(G2HttpError.Code.ENGINE_UNAVAILABLE, failure.httpError().orElseThrow().code());
            assertArrayEquals(G2Wire.encodeError(fixture.refusal()), failure.responseBytes());
            assertEquals(result.summary(), G2ClientBatchWire.decode(G2ClientBatchWire.encode(result.summary())));
        }
    }

    @Test void malformedResponseStopsAtOriginalUnverifiedPrefix() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client()) {
            fixture.malformedAt = 2;
            AtomicInteger produced = new AtomicInteger();
            var result = new G2ClientBatchSession(client, SOURCE.machineId()).run(BUDGET,
                    preceding -> new G2ClientBatchSession.Evaluate(request(produced.getAndIncrement())), evaluated -> { });
            assertEquals(Optional.of(G2ClientException.Reason.RESPONSE_UNVERIFIED), result.summary().clientFailureReason());
            assertEquals(2, produced.get()); assertEquals(2, fixture.calls.get());
            assertEquals(1, result.summary().consumedResponses());
            assertEquals("batch-0", result.lastVerified().orElseThrow().response().requestId());
        }
    }

    @Test void totalBatchDeadlineClipsActualHttpWaitAndNeverRetriesUnknown() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client()) {
            fixture.stallAt = 1;
            AtomicInteger produced = new AtomicInteger();
            long tick = System.nanoTime();
            var result = new G2ClientBatchSession(client, SOURCE.machineId()).run(new G2ClientBatchSession.Budget(4, Duration.ofMillis(400)),
                    preceding -> new G2ClientBatchSession.Evaluate(request(produced.getAndIncrement())), evaluated -> fail());
            assertEquals(Optional.of(G2ClientException.Reason.TRANSPORT_UNKNOWN), result.summary().clientFailureReason());
            assertTrue(fixture.headersSent.await(1, TimeUnit.SECONDS));
            assertTrue(System.nanoTime() - tick < Duration.ofMillis(2500).toNanos(), "clipped to batch budget, not 3 second client budget");
            assertEquals(1, fixture.calls.get()); assertEquals(1, produced.get());
            assertEquals(0, result.summary().verifiedResponses());
        }
    }

    @Test void consumerFailurePreservesVerifiedButUnconsumedResponseAndStops() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client()) {
            AtomicInteger produced = new AtomicInteger();
            IllegalStateException expected = new IllegalStateException("consumer persistence failed");
            var result = new G2ClientBatchSession(client, SOURCE.machineId()).run(BUDGET,
                    preceding -> new G2ClientBatchSession.Evaluate(request(produced.getAndIncrement())), evaluated -> { throw expected; });
            assertEquals(G2ClientBatchSession.Stop.CONSUMER_FAILED, result.summary().stop());
            assertSame(expected, result.failure().orElseThrow());
            assertEquals(1, result.summary().verifiedResponses()); assertEquals(0, result.summary().consumedResponses());
            assertEquals(1, produced.get()); assertEquals(1, fixture.calls.get());
        }
    }

    @Test void consumerTurnaroundUsesOriginalBatchClockAndCannotResetTheDeadline() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client()) {
            AtomicInteger produced = new AtomicInteger();
            var result = new G2ClientBatchSession(client, SOURCE.machineId()).run(new G2ClientBatchSession.Budget(4, Duration.ofSeconds(1)),
                    preceding -> new G2ClientBatchSession.Evaluate(request(produced.getAndIncrement())), evaluated -> {
                        try { Thread.sleep(1100); }
                        catch (InterruptedException error) { Thread.currentThread().interrupt(); throw new IllegalStateException(error); }
                    });
            assertEquals(G2ClientBatchSession.Stop.DEADLINE, result.summary().stop());
            assertEquals(1, produced.get()); assertEquals(1, fixture.calls.get());
            assertEquals(1, result.summary().consumedResponses());
            assertTrue(result.summary().elapsedNanos() >= Duration.ofMillis(1100).toNanos());
        }
    }

    @Test void producerFailureAndReentrantBatchNeverInvokeHttp() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client()) {
            G2ClientBatchSession session = new G2ClientBatchSession(client, SOURCE.machineId());
            IllegalArgumentException failure = new IllegalArgumentException("no current input");
            var result = session.run(BUDGET, preceding -> { throw failure; }, evaluated -> fail());
            assertEquals(G2ClientBatchSession.Stop.PRODUCER_FAILED, result.summary().stop());
            assertSame(failure, result.failure().orElseThrow());
            var reentrant = session.run(BUDGET, preceding -> {
                session.run(BUDGET, ignored -> G2ClientBatchSession.Complete.INSTANCE, evaluated -> fail());
                return G2ClientBatchSession.Complete.INSTANCE;
            }, evaluated -> fail());
            assertEquals(G2ClientBatchSession.Stop.PRODUCER_FAILED, reentrant.summary().stop());
            assertEquals(0, fixture.calls.get());
        }
    }

    @Test void requestBoundDoesNotSubmitTheNextLazyCandidate() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client()) {
            AtomicInteger produced = new AtomicInteger();
            var result = new G2ClientBatchSession(client, SOURCE.machineId()).run(new G2ClientBatchSession.Budget(2, Duration.ofSeconds(5)),
                    preceding -> new G2ClientBatchSession.Evaluate(request(produced.getAndIncrement())), evaluated -> { });
            assertEquals(G2ClientBatchSession.Stop.REQUEST_BOUND, result.summary().stop());
            assertEquals(3, produced.get()); assertEquals(2, fixture.calls.get());
            assertEquals(Optional.of("batch-2"), result.summary().lastRequestId());
            assertEquals(2, result.summary().consumedResponses());
        }
    }

    @Test void interruptedEntryPreservesFlagAndInvokesNeitherCallbackNorHttp() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client()) {
            Thread.currentThread().interrupt();
            try {
                var result = new G2ClientBatchSession(client, SOURCE.machineId()).run(BUDGET, preceding -> { fail(); return null; }, evaluated -> fail());
                assertEquals(G2ClientBatchSession.Stop.INTERRUPTED, result.summary().stop());
                assertTrue(Thread.currentThread().isInterrupted()); assertEquals(0, fixture.calls.get());
            } finally { Thread.interrupted(); }
        }
    }

    @Test void originalSuccessfulBodyIsDefensiveAndCannotBeReplacedByReencoding() throws Exception {
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client()) {
            G2Evaluation evaluated = client.evaluateWithEvidence(request(0));
            byte[] changed = evaluated.responseBytes(); changed[0] = 0;
            assertEquals('{', evaluated.responseBytes()[0]);
            assertThrows(IllegalArgumentException.class, () -> new G2Evaluation(evaluated.response(), evaluated.evidence(), changed));
            byte[] original = evaluated.responseBytes();
            G2Evaluation copied = new G2Evaluation(evaluated.response(), evaluated.evidence(), original);
            original[0] = 0; assertEquals('{', copied.responseBytes()[0]);
            G2Response other = new G2Response("other-id", evaluated.response().milestone(), SOURCE, evaluated.response().result());
            assertThrows(IllegalArgumentException.class, () -> new G2Evaluation(other, evaluated.evidence(), evaluated.responseBytes()));
        }
    }

    @Test void strictSummaryRoundtripRejectsWrongMissingNullAndUnsafeNumericTokens() {
        var summary = new G2ClientBatchSession.Summary(SOURCE.machineId(), Instant.parse("2026-10-22T23:00:00Z"), Instant.parse("2026-10-22T23:00:01Z"),
                Long.MAX_VALUE, G2ClientBatchSession.Stop.COMPLETE, 0, 0, 0, Optional.empty(), Optional.empty());
        byte[] encoded = G2ClientBatchWire.encode(summary);
        assertEquals(summary, G2ClientBatchWire.decode(encoded));
        String wire = new String(encoded, StandardCharsets.UTF_8);
        for (String wrong : List.of(
                wire.replace("\"submitted_requests\":0", "\"submitted_requests\":false"),
                wire.replace("\"submitted_requests\":0", "\"submitted_requests\":0.0"),
                wire.replace("\"submitted_requests\":0", "\"submitted_requests\":\"0\""),
                wire.replace("\"submitted_requests\":0,", ""),
                wire.replace("\"elapsed_nanos\":\"9223372036854775807\"", "\"elapsed_nanos\":9223372036854775807"),
                wire.replace("\"elapsed_nanos\":\"9223372036854775807\"", "\"elapsed_nanos\":\"01\""),
                wire.replace("\"elapsed_nanos\":\"9223372036854775807\"", "\"elapsed_nanos\":\"9223372036854775808\""),
                wire.replace("\"stop\":\"COMPLETE\"", "\"stop\":\"CLIENT_FAILED\""),
                wire.replace("\"last_request_id\":null", "\"last_request_id\":[]"),
                wire.replace("\"schema\":", "\"extra\":null,\"schema\":"))) {
            assertThrows(IllegalArgumentException.class, () -> G2ClientBatchWire.decode(bytes(wrong)));
        }
    }

    @Test void invalidBudgetsRemainLocalAndCannotInvokeHttp() throws Exception {
        assertThrows(IllegalArgumentException.class, () -> new G2ClientBatchSession.Budget(0, Duration.ofSeconds(1)));
        assertThrows(IllegalArgumentException.class, () -> new G2ClientBatchSession.Budget(1025, Duration.ofSeconds(1)));
        assertThrows(IllegalArgumentException.class, () -> new G2ClientBatchSession.Budget(1, Duration.ZERO));
        assertThrows(IllegalArgumentException.class, () -> new G2ClientBatchSession.Budget(1, Duration.ofSeconds(Long.MAX_VALUE)));
        try (Fixture fixture = new Fixture(); G2JavaClient client = fixture.client()) {
            assertThrows(IllegalArgumentException.class, () -> new G2ClientConfig(URI.create("http://127.0.0.1:8089"), Duration.ofSeconds(1), G2Wire.MAX_RESPONSE_BYTES + 1));
            G2ClientException failure = assertThrows(G2ClientException.class, () -> client.evaluateWithEvidence(request(0), Duration.ZERO));
            assertEquals(G2ClientException.Reason.LOCAL_REQUEST_INVALID, failure.reason());
            assertFalse(failure.evidence().actualHttpInvoked()); assertEquals(0, fixture.calls.get());
            G2ClientException expired = assertThrows(G2ClientException.class, () -> client.evaluateWithEvidence(request(0), Duration.ofNanos(1)));
            assertEquals(G2ClientException.Reason.LOCAL_DEADLINE_EXPIRED, expired.reason());
            assertFalse(expired.evidence().actualHttpInvoked()); assertEquals(0, fixture.calls.get());
        }
    }

    private static final class Fixture implements AutoCloseable {
        private final HttpServer server;
        private final java.util.concurrent.ExecutorService executor = Executors.newCachedThreadPool();
        private final AtomicInteger calls = new AtomicInteger();
        private final List<byte[]> requests = Collections.synchronizedList(new ArrayList<>());
        private final Set<Integer> remotePorts = Collections.synchronizedSet(new HashSet<>());
        private final CountDownLatch headersSent = new CountDownLatch(1), release = new CountDownLatch(1);
        private volatile int rejectAt, malformedAt, stallAt;
        Fixture() throws IOException {
            server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
            server.createContext(G2Wire.HTTP_PATH, this::handle); server.setExecutor(executor); server.start();
        }
        G2JavaClient client() {
            return new G2JavaClient(new G2ClientConfig(URI.create("http://127.0.0.1:" + server.getAddress().getPort()), Duration.ofSeconds(3), G2Wire.MAX_RESPONSE_BYTES));
        }
        G2HttpError refusal() { return new G2HttpError(G2HttpError.SCHEMA, G2HttpError.Code.ENGINE_UNAVAILABLE, "synthetic domain unavailable"); }
        private void handle(HttpExchange exchange) throws IOException {
            int index = calls.incrementAndGet();
            try (exchange) {
                remotePorts.add(exchange.getRemoteAddress().getPort());
                byte[] rawRequest = exchange.getRequestBody().readAllBytes(); requests.add(rawRequest);
                G2Request input = G2Wire.decodeRequest(rawRequest);
                boolean reject = index == rejectAt;
                byte[] raw = reject ? G2Wire.encodeError(refusal()) : G2Wire.encodeResponse(new G2Response(input.requestId(), input.milestone(), input.source(), input.payload()));
                if (index == malformedAt) raw = bytes("{\"schema\":true}");
                exchange.getResponseHeaders().set("Content-Type", "application/json; charset=utf-8");
                exchange.getResponseHeaders().set("X-Xar-Producer", G2Wire.PRODUCER);
                exchange.getResponseHeaders().set("X-Xar-Producer-Version", G2Wire.PRODUCER_VERSION);
                exchange.getResponseHeaders().set("X-Xar-Contract-Revision", G2Wire.REQUEST_SCHEMA);
                exchange.sendResponseHeaders(reject ? refusal().code().httpStatus() : 200, raw.length);
                if (index == stallAt) {
                    exchange.getResponseBody().write(raw, 0, 1); exchange.getResponseBody().flush(); headersSent.countDown();
                    try { release.await(5, TimeUnit.SECONDS); } catch (InterruptedException error) { Thread.currentThread().interrupt(); }
                } else exchange.getResponseBody().write(raw);
            }
        }
        @Override public void close() { release.countDown(); server.stop(0); executor.shutdownNow(); }
    }
}
