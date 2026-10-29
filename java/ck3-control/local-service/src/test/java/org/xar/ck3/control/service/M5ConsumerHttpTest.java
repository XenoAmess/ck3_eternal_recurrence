package org.xar.ck3.control.service;

import static org.junit.jupiter.api.Assertions.*;

import io.quarkus.test.common.http.TestHTTPResource;
import io.quarkus.test.junit.QuarkusTest;
import java.io.IOException;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.Duration;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.g2.client.G2ClientConfig;
import org.xar.ck3.control.g2.client.G2ClientException;
import org.xar.ck3.control.g2.client.G2JavaClient;
import org.xar.ck3.control.g2.common.G2HttpError;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m5.M5DecisionConsumer;
import org.xar.ck3.control.g2.m5.M5PayloadCodec;
import org.xar.ck3.control.g2.m5.M5Research;
import org.xar.ck3.control.g2.m5.M5FrameDispatcher;
import org.xar.ck3.control.g2.m5.M5ReservationCodec;
import org.xar.ck3.control.g2.m5.M5ReservationConsumer;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.object;

/** The same Quarkus host and typed client reach the real M5 consumer and local test checkpoint. */
@QuarkusTest
class M5ConsumerHttpTest {
    @TestHTTPResource(G2Wire.HTTP_PATH) URI endpoint;
    @TempDir Path checkpoint;

    @Test void realHostClientM5ConsumerAndSavedJsonPreserveOriginalCandidateAssertions() throws Exception {
        G2Request request = G2Wire.decodeRequest(fixture("M5.request.json"));
        M5Research.Result expected = M5PayloadCodec.decodeResult(fixture("M5.expected-result.json"));
        assertEquals(Milestone.M5, request.milestone());
        try (G2JavaClient client = client()) {
            G2Response response = client.evaluate(request);
            assertEquals(request.requestId(), response.requestId());
            assertEquals(request.source(), response.source());
            assertEquals(Milestone.M5, response.milestone());
            M5Research.Result result = M5PayloadCodec.decodeResult(response.result().bytes());
            assertEquals(expected.intakeAnalysis(), result.intakeAnalysis(), "complete original producer and selector assertions");
            assertEquals(expected.participatingWars(), result.participatingWars(), "current participant facts and unknown scope");
            assertEquals(expected.existingWarPlan(), result.existingWarPlan(), "original plan missing/null/object semantics");
            M5DecisionConsumer.Consumption consumed = M5DecisionConsumer.consume(response.result().bytes());
            assertFalse(consumed.actionAuthorized());
            Path savedPath = checkpoint.resolve("m5-response.json");
            byte[] savedBytes = G2Wire.encodeResponse(response);
            Files.write(savedPath, savedBytes, StandardOpenOption.CREATE_NEW);
            byte[] actualSavedBytes = Files.readAllBytes(savedPath);
            assertArrayEquals(savedBytes, actualSavedBytes);
            G2Response saved = G2Wire.decodeResponse(actualSavedBytes);
            assertArrayEquals(response.result().bytes(), saved.result().bytes(), "HTTP and persistence retain original JSON tokens");
            assertEquals(consumed, M5DecisionConsumer.consume(saved.result().bytes()), "saved evidence reaches the same real consumer");
            var selector = object(result.intakeAnalysis().get("selector_request"), "actual selector request");
            M5FrameDispatcher owner = new M5FrameDispatcher(request.source(), object(selector.get("snapshot"), "owner snapshot"),
                    object(selector.get("commitments"), "owner commitments"));
            var reserved = M5ReservationConsumer.reserve(request, saved, owner);
            assertEquals(M5FrameDispatcher.Status.reserved_observed_analytic, reserved.status());
            assertEquals(result.intakeAnalysis().get("analysis"), reserved.analysis().orElseThrow());
            assertFalse(reserved.formalActionReady());
            assertFalse(reserved.intentDurable());
            Path reservationPath = checkpoint.resolve("m5-analytic-reservation.json");
            Files.write(reservationPath, M5ReservationCodec.encode(reserved), StandardOpenOption.CREATE_NEW);
            assertEquals(reserved, M5ReservationCodec.decode(Files.readAllBytes(reservationPath)));
            var repeated = M5ReservationConsumer.reserve(request, saved, owner);
            assertEquals(M5FrameDispatcher.Status.already_reserved_this_frame, repeated.status());
            assertEquals(reserved.reservation(), repeated.reservation());
            assertEquals(request.source(), owner.resourceSnapshot().source());
            assertEquals(reserved.reservation().orElseThrow().commitmentsAfter(), owner.resourceSnapshot().commitments());
            assertFalse(StrictJson.parse(saved.result().bytes(), M5PayloadCodec.MAXIMUM_BYTES)
                    .get("scope").get("resource_reservation_performed").booleanValue(),
                    "a separate caller-side reservation must never rewrite the pure HTTP analysis as a reservation");
        }
    }

    @Test void m5UnknownOperationIsAnActualTypedHttpRejectionAtTheSameHost() throws IOException {
        G2Request request = G2Wire.decodeRequest(fixture("M5.rejected-request.json"));
        try (G2JavaClient client = client()) {
            G2ClientException refusal = assertThrows(G2ClientException.class, () -> client.evaluate(request));
            assertEquals(G2ClientException.Reason.HTTP_REJECTED, refusal.reason());
            assertTrue(refusal.evidence().actualHttpInvoked());
            assertTrue(refusal.evidence().responseComplete());
            assertEquals(G2HttpError.Code.DOMAIN_REJECTED, refusal.httpError().orElseThrow().code());
        }
    }

    @Test void lifecycleProposedUnknownAndChangedBodyReachTheSameHostAsSuccessfulDomainResults() throws Exception {
        List<String> names = List.of("M5.lifecycle-proposed", "M5.lifecycle-unknown", "M5.lifecycle-conflict");
        List<String> statuses = List.of("PROPOSED", "DEFERRED", "BODY_CONFLICT");
        try (G2JavaClient client = client()) {
            for (int index = 0; index < names.size(); index++) {
                String name = names.get(index);
                G2Request request = G2Wire.decodeRequest(fixture(name + ".request.json"));
                G2Response response = client.evaluate(request);
                assertArrayEquals(fixture(name + ".expected-result.json"), response.result().bytes());
                var result = StrictJson.parse(response.result().bytes(), M5PayloadCodec.MAXIMUM_BYTES);
                assertEquals(statuses.get(index), result.get("status").textValue());
                assertFalse(result.get("formal_action_ready").booleanValue());
                assertFalse(result.get("resource_reservation_performed").booleanValue());
                assertFalse(result.get("intent_durable").booleanValue());
                Path saved = checkpoint.resolve(name + ".response.json");
                Files.write(saved, G2Wire.encodeResponse(response), StandardOpenOption.CREATE_NEW);
                assertArrayEquals(response.result().bytes(), G2Wire.decodeResponse(Files.readAllBytes(saved)).result().bytes());
                if (index == 1) assertEquals("EXISTING_UNKNOWN", result.get("deferred_reason").textValue());
            }
        }
    }

    private G2JavaClient client() {
        return new G2JavaClient(new G2ClientConfig(URI.create("http://127.0.0.1:" + endpoint.getPort()),
                Duration.ofSeconds(20), G2Wire.MAX_RESPONSE_BYTES));
    }

    private static byte[] fixture(String name) throws IOException {
        try (var source = M5ConsumerHttpTest.class.getResourceAsStream("/g2-http/" + name)) {
            assertNotNull(source, "actual captured M5 producer/consumer fixture is required: " + name);
            byte[] raw = source.readNBytes(G2Wire.MAX_RESPONSE_BYTES + 1);
            assertTrue(raw.length > 0 && raw.length <= G2Wire.MAX_RESPONSE_BYTES, "finite complete M5 fixture required");
            return raw;
        }
    }
}
