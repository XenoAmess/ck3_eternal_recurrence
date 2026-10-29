package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;
import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusTest;
import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.time.Instant;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.xar.ck3.control.g2.client.G2ClientConfig;
import org.xar.ck3.control.build.WindowsJobProcess;
import org.xar.ck3.control.g2.client.G2JavaClient;
import org.xar.ck3.control.g2.client.G2Evaluation;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.m4.M4OrdinaryConstructionPort;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstruction;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionCodec;
import org.xar.ck3.control.wave3.development.wartimesequencing.OrdinaryWartimeConstructionConsumer;

/** Actual single-host HTTP/client/consumer test. Missing actual producer pairs fail instead of skipping. */
@QuarkusTest
class M4OrdinaryConstructionHttpTest {
    @TestHTTPResource(G2Wire.HTTP_PATH) URI endpoint;

    @ParameterizedTest
    @ValueSource(strings = {"exact_ample_threshold", "market_unavailable"})
    void actualOrdinaryProducerPairTraversesTheExistingHostClientAndFreshConsumer(String name) throws Exception {
        byte[] requestBytes = fixture(name + "-request.json"), expectedBytes = fixture(name + "-response.json");
        var request = G2Wire.decodeRequest(requestBytes); var expected = G2Wire.decodeResponse(expectedBytes);
        assertEquals(Milestone.M4, request.milestone()); assertEquals(request.source(), expected.source());
        URI base = URI.create("http://127.0.0.1:" + endpoint.getPort());
        try (G2JavaClient client = new G2JavaClient(new G2ClientConfig(base, Duration.ofSeconds(20), G2Wire.MAX_RESPONSE_BYTES))) {
            var actual = client.evaluateWithEvidence(request);
            assertTrue(actual.evidence().actualHttpInvoked()); assertTrue(actual.evidence().responseComplete());
            assertEquals(200, actual.evidence().httpStatus().orElseThrow());
            assertArrayEquals(expectedBytes, actual.responseBytes(), "actual HTTP must retain the exact original producer response bytes");
            assertEquals(request.requestId(), actual.response().requestId()); assertEquals(request.source(), actual.response().source());
            var consumed = OrdinaryWartimeConstructionCodec.verifyResponse(request.payload().bytes(), actual.response().result().bytes());
            assertEquals(Optional.of("life-advance"), consumed.selectedStep()); assertTrue(consumed.continueOrdinaryPlanner()); assertFalse(consumed.canSubmitAction());
            assertEquals(OrdinaryWartimeConstruction.Disposition.DEFER_OPTIONAL_CONSTRUCTION, consumed.disposition());
            if (name.equals("exact_ample_threshold")) assertEquals("FINANCING_OBSERVATION_UNAVAILABLE", consumed.reason().orElseThrow().name());
            byte[] persisted = G2Wire.encodeResponse(actual.response()); assertArrayEquals(actual.responseBytes(), persisted);
            OrdinaryWartimeConstructionCodec.verifyResponse(request.payload().bytes(), G2Wire.decodeResponse(persisted).result().bytes());

            AtomicInteger reads = new AtomicInteger(), optionalQuotes = new AtomicInteger();
            AtomicInteger portCalls = new AtomicInteger();
            AtomicReference<G2Evaluation> freshExchange = new AtomicReference<>();
            M4OrdinaryConstructionPort port = new M4OrdinaryConstructionPort(current -> {
                portCalls.incrementAndGet(); var evaluated = client.evaluateWithEvidence(current); freshExchange.set(evaluated); return evaluated.response();
            }, () -> new M4OrdinaryConstructionPort.Context("actual-fresh-consumer-" + name, request.source()));
            var fresh = OrdinaryWartimeConstructionConsumer.plan(() -> {
                reads.incrementAndGet(); return new OrdinaryWartimeConstructionCodec.ObservedRequest(request.payload().bytes());
            }, () -> {
                optionalQuotes.incrementAndGet(); return new OrdinaryWartimeConstructionConsumer.UnavailableQuote(
                        OrdinaryWartimeConstructionConsumer.UnavailableReason.CURRENT_SOURCE_UNAVAILABLE);
            }, port);
            assertEquals(1, reads.get()); assertEquals(0, optionalQuotes.get(), "missing financing observation must defer before the optional quote");
            assertEquals(1, portCalls.get(), "the fresh actual consumer must evaluate through the registered HTTP port");
            G2Evaluation freshHttp = java.util.Objects.requireNonNull(freshExchange.get());
            assertTrue(freshHttp.evidence().actualHttpInvoked()); assertTrue(freshHttp.evidence().responseComplete());
            assertEquals(200, freshHttp.evidence().httpStatus().orElseThrow());
            assertEquals(OrdinaryWartimeConstruction.Disposition.DEFER_OPTIONAL_CONSTRUCTION, fresh.disposition());
            assertEquals(Optional.of("life-advance"), fresh.selectedStep()); assertTrue(fresh.continueOrdinaryPlanner());
            OrdinaryWartimeConstructionCodec.verifyResponse(request.payload().bytes(), actual.response().result().bytes());
            String retained = System.getProperty("xar.g2.http.evidence-dir");
            if (retained != null) {
                Path root = Path.of(retained); Files.createDirectories(root);
                Path directory = Files.createDirectory(root.resolve("M4-ordinary-" + name));
                Files.write(directory.resolve("actual-producer.request.json"), requestBytes, StandardOpenOption.CREATE_NEW);
                Files.write(directory.resolve("producer.response.json"), expectedBytes, StandardOpenOption.CREATE_NEW);
                Files.write(directory.resolve("actual-http.original-response.json"), actual.responseBytes(), StandardOpenOption.CREATE_NEW);
                Files.write(directory.resolve("fresh-consumer.result.json"), OrdinaryWartimeConstructionCodec.encode(fresh), StandardOpenOption.CREATE_NEW);
                Files.write(directory.resolve("fresh-consumer.actual-http.original-response.json"), freshHttp.responseBytes(), StandardOpenOption.CREATE_NEW);
                var json = new com.fasterxml.jackson.databind.ObjectMapper();
                Files.write(directory.resolve("actual-http.json"), json.writeValueAsBytes(proof(actual)), StandardOpenOption.CREATE_NEW);
                Files.write(directory.resolve("fresh-consumer.actual-http.json"), json.writeValueAsBytes(proof(freshHttp)), StandardOpenOption.CREATE_NEW);
            }
        }
    }
    private record ActualHttp(String schema, String machine_id, String observed_at_utc, String endpoint, String requestId,
            String startedAtUtc, String completedAtUtc, long elapsedNanos, String requestSha256, String originalResponseSha256,
            int httpStatus, boolean responseComplete, boolean actualHttpInvoked, int newGameDays) { }
    private static ActualHttp proof(G2Evaluation actual) {
        return new ActualHttp("xar.m4-ordinary-quarkus-http-actual.v1", WindowsJobProcess.currentMachineId(),
                Instant.now().toString(), actual.evidence().endpoint().toString(), actual.evidence().requestId(),
                actual.evidence().startedAtUtc().toString(), actual.evidence().completedAtUtc().toString(), actual.evidence().elapsedNanos(),
                actual.evidence().requestSha256(), actual.evidence().retainedResponseSha256(),
                actual.evidence().httpStatus().orElseThrow(), actual.evidence().responseComplete(), actual.evidence().actualHttpInvoked(), 0);
    }

    private static byte[] fixture(String name) throws IOException {
        try (InputStream input = M4OrdinaryConstructionHttpTest.class.getResourceAsStream("/g2-http/m4ordinary/" + name)) {
            if (input == null) throw new IOException("required actual M4 ordinary producer export missing: " + name);
            byte[] raw = input.readNBytes(G2Wire.MAX_RESPONSE_BYTES + 1);
            if (raw.length == 0 || raw.length > G2Wire.MAX_RESPONSE_BYTES) throw new IOException("bounded actual producer bytes required");
            return raw;
        }
    }
}
