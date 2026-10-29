package org.xar.ck3.control.wave2.runtime.deadlinetransport;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

final class DeadlineTransportProjectionPortTest {
    private static final int CORPUS_MAX_BYTES = 196_608;
    private static final JsonNode CORPUS = corpus();
    private final DeadlineTransportProjectionPort port = new DeadlineTransportProjectionPort();

    @TestFactory
    Stream<DynamicTest> actualReturnedProducerProofsTraverseTheRegisteredTypedPort() {
        return java.util.stream.StreamSupport.stream(CORPUS.path("transport_cases").spliterator(), false)
                .filter(row -> "returned".equals(row.at("/outcome/status").textValue()))
                .map(row -> DynamicTest.dynamicTest(row.path("id").textValue(), () -> {
                    byte[] raw = payload(row);
                    DeadlineTransport.Observation observed = port.project(port.decode(raw));
                    assertFalse(observed.nativeAdmissionGranted());
                    assertFalse(observed.replayAllowed());
                    assertEquals(0, observed.savedDayCredit());
                    byte[] javaClock = port.encode(observed);
                    assertEquals(row.at("/outcome/value"), StrictJson.parse(javaClock));
                    RegisteredProjection registered = new DeadlineTransportProjectionCatalog().registrations().getFirst();
                    ProjectionResult response = registered.execute(call(raw));
                    ProjectionResult.Succeeded success = assertInstanceOf(ProjectionResult.Succeeded.class, response);
                    assertEquals(ProjectionOperation.DEADLINE_TRANSPORT_PROJECT, success.identity().operation());
                    assertEquals(StrictJson.parse(javaClock), StrictJson.parse(success.result().bytes()));
                }));
    }

    @Test
    void oneDomainCatalogRegistersOnlyTheDeadlineOperation() {
        var entries = new DeadlineTransportProjectionCatalog().registrations();
        assertEquals(1, entries.size());
        assertEquals(ProjectionOperation.DEADLINE_TRANSPORT_PROJECT, entries.getFirst().operation());
        assertEquals(65_536, port.inputMaximumBytes());
        assertEquals(65_536, port.outputMaximumBytes());
        assertEquals(196_608, CORPUS_MAX_BYTES);
        assertEquals(9, CORPUS.path("transport_cases").size());
        assertEquals(7, java.util.stream.StreamSupport.stream(CORPUS.path("transport_cases").spliterator(), false)
                .filter(row -> "returned".equals(row.at("/outcome/status").textValue())).count());
        assertEquals(10, CORPUS.path("original_tests").intValue());
        assertEquals(0, CORPUS.path("original_skipped").intValue());
    }

    @Test
    void exactPayloadAndRawNumericTokensRemainDomainValidated() {
        ObjectNode payload = payloadNode(returned("changed-speed-five-day"));
        payload.put("unmigrated_alias", true);
        assertInvalidPayload(payload);
        ObjectNode floatSpeed = payloadNode(returned("changed-speed-five-day"));
        ((ObjectNode) floatSpeed.get("request")).put("speed", 5.0);
        assertInvalidPayload(floatSpeed);
        ObjectNode floatGeneration = payloadNode(returned("changed-speed-five-day"));
        ((ObjectNode) floatGeneration.at("/completion/clock/armed")).put("generation", 7.0);
        assertInvalidPayload(floatGeneration);
        ObjectNode falseQualification = payloadNode(returned("changed-speed-five-day"));
        ((ObjectNode) falseQualification.at("/completion/clock")).put("exact_one_day_qualification_claimed", true);
        assertInvalidPayload(falseQualification);
    }

    @Test
    void registryRejectsOversizedApiPayloadEvenThoughTheCorpusHasItsOwnLargerBudget() {
        byte[] oversized = ("{\"padding\":\"" + "x".repeat(65_536) + "\"}").getBytes(StandardCharsets.UTF_8);
        ProjectionCall input = new ProjectionCall(new ProjectionCall.Identity("deadline-oversize",
                ProjectionOperation.DEADLINE_TRANSPORT_PROJECT), ProjectionJson.object(oversized, CORPUS_MAX_BYTES));
        ProjectionResult response = new DeadlineTransportProjectionCatalog().registrations().getFirst().execute(input);
        ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class, response);
        assertEquals(ProjectionError.Code.PAYLOAD_TOO_LARGE, rejected.error().code());
    }

    @Test
    void explicitPostconditionRefusalsAndOpaqueNumericTypesKeepTheirErrorContracts() {
        ObjectNode input = payloadNode(returned("early-event-two-days"));
        ObjectNode clockCancel = (ObjectNode) input.at("/completion/clock/early_boundary_cancel");
        clockCancel.put("opaque_decimal", 1.0);
        JsonNode actions = input.at("/completion/actions");
        ObjectNode actionCancel = (ObjectNode) actions.get(actions.size() - 1).get("result");
        actionCancel.put("opaque_decimal", 1.0);
        byte[] result = port.encode(port.project(port.decode(LegacyJsonValues.encode(input))));
        assertTrue(new String(result, StandardCharsets.UTF_8).contains("\"opaque_decimal\":1.0"));
        assertEquals(StrictJson.parse(result), StrictJson.parse(
                port.encode(port.project(port.decode(LegacyJsonValues.encode(input))))));
        actionCancel.put("opaque_decimal", 1);
        assertObservationRejected(input);
        ObjectNode missingCancel = payloadNode(returned("early-event-two-days"));
        ((ObjectNode) missingCancel.at("/completion/clock")).putNull("early_boundary_cancel");
        assertObservationRejected(missingCancel);
        ObjectNode unpaused = payloadNode(returned("changed-speed-five-day"));
        ((ObjectNode) unpaused.at("/completion/current_frame")).put("paused", false);
        assertObservationRejected(unpaused);
        assertThrows(NullPointerException.class, () -> port.project(null));
    }

    private void assertInvalidPayload(ObjectNode input) {
        byte[] raw = LegacyJsonValues.encode(input);
        assertThrows(ContractViolationException.class, () -> port.decode(raw));
        ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class,
                new DeadlineTransportProjectionCatalog().registrations().getFirst().execute(call(raw)));
        assertEquals(ProjectionError.Code.INVALID_PAYLOAD, rejected.error().code());
    }

    private void assertObservationRejected(ObjectNode input) {
        byte[] raw = LegacyJsonValues.encode(input);
        DeadlineTransportProjectionPort.Input decoded = port.decode(raw);
        var original = assertThrows(DeadlineTransport.ObservationRejection.class,
                () -> DeadlineTransport.observe(decoded.request(), decoded.completion()));
        var marker = assertThrows(ProjectionDomainRejection.class, () -> port.project(decoded));
        assertEquals(original.getMessage(), marker.getMessage());
        ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class,
                new DeadlineTransportProjectionCatalog().registrations().getFirst().execute(call(raw)));
        assertEquals(ProjectionError.Code.DOMAIN_REJECTED, rejected.error().code());
        assertEquals(original.getMessage(), rejected.error().message());
    }

    private static ProjectionCall call(byte[] raw) {
        return new ProjectionCall(new ProjectionCall.Identity("deadline-producer-consumer",
                ProjectionOperation.DEADLINE_TRANSPORT_PROJECT), ProjectionJson.object(raw, 65_536));
    }

    private static ObjectNode payloadNode(JsonNode row) {
        ObjectNode payload = StrictJson.object();
        payload.set("request", row.get("request").deepCopy());
        payload.set("completion", row.get("completion").deepCopy());
        return payload;
    }

    private static byte[] payload(JsonNode row) { return LegacyJsonValues.encode(payloadNode(row)); }

    private static JsonNode returned(String id) {
        for (JsonNode row : CORPUS.path("transport_cases")) {
            if (id.equals(row.path("id").textValue())) { return row; }
        }
        throw new IllegalStateException("mandatory real producer row is missing: " + id);
    }

    private static JsonNode corpus() {
        try (InputStream stream = DeadlineTransportProjectionPortTest.class.getResourceAsStream(
                "/deadlinetransport/producer-golden.json")) {
            if (stream == null) { throw new IllegalStateException("mandatory actual producer corpus is missing"); }
            byte[] raw = stream.readNBytes(CORPUS_MAX_BYTES + 1);
            if (raw.length > CORPUS_MAX_BYTES) { throw new IllegalStateException("deadline corpus exceeds independent role budget"); }
            JsonNode result = StrictJson.parse(raw, CORPUS_MAX_BYTES);
            if (!"deadline-transport-producer-corpus/v1".equals(result.path("corpus_profile").textValue())) {
                throw new IllegalStateException("deadline producer corpus profile differs");
            }
            if (!result.path("corpus_maximum_bytes").isIntegralNumber()
                    || result.path("corpus_maximum_bytes").intValue() != CORPUS_MAX_BYTES) {
                throw new IllegalStateException("deadline producer corpus role budget differs");
            }
            return result;
        } catch (IOException error) {
            throw new IllegalStateException("cannot read actual producer corpus", error);
        }
    }
}
