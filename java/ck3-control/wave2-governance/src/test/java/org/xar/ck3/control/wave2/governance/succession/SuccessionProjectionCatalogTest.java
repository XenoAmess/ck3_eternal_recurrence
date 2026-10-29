package org.xar.ck3.control.wave2.governance.succession;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ServiceLoader;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.projection.*;
import static org.junit.jupiter.api.Assertions.*;

final class SuccessionProjectionCatalogTest {
    @TestFactory Stream<DynamicTest> originalProducerVectorsThroughRegisteredTypedPorts() throws IOException {
        JsonNode source = golden();
        return StreamSupport.stream(source.get("cases").spliterator(), false)
                .filter(row -> !row.get("request").get("operation").textValue().equals("operating"))
                .map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
                    JsonNode request = row.get("request"); ProjectionOperation operation = operation(request.get("operation").textValue());
                    ProjectionResult result = registered(operation).execute(call(operation, SuccessionCodec.encode(request)));
                    ProjectionResult.Succeeded success = assertInstanceOf(ProjectionResult.Succeeded.class, result);
                    assertEquals(row.get("expected"), SuccessionCodec.parse(success.result().bytes()));
                }));
    }
    @Test void realServiceDescriptorAndRoleBudgetsArePartOfTheDomainArtifact() {
        assertTrue(ServiceLoader.load(ProjectionPortCatalog.class).stream().anyMatch(provider -> provider.type().equals(SuccessionProjectionCatalog.class)));
        assertEquals(3, new SuccessionProjectionCatalog().registrations().size());
        var port = new SuccessionProjectionCatalog.FreezePort();
        assertEquals(SuccessionCodec.MAX_BYTES, port.inputMaximumBytes()); assertEquals(SuccessionCodec.MAX_BYTES, port.outputMaximumBytes());
    }
    @Test void rawCoercedRevisionAndMisroutedPayloadFailInsideTheRegisteredCodec() throws IOException {
        JsonNode row = StreamSupport.stream(golden().get("cases").spliterator(), false)
                .filter(value -> value.get("name").textValue().equals("normalize_complete_retained_expectation")).findFirst().orElseThrow();
        String original = new String(SuccessionCodec.encode(row.get("request")), StandardCharsets.UTF_8);
        for (String token : new String[]{"true", "7.0", "\"7\""}) {
            String changed = original.replace("\"revision\":7", "\"revision\":" + token); assertNotEquals(original, changed);
            assertInstanceOf(ProjectionResult.Rejected.class, registered(ProjectionOperation.SUCCESSION_NORMALIZE)
                    .execute(call(ProjectionOperation.SUCCESSION_NORMALIZE, changed.getBytes(StandardCharsets.UTF_8))));
        }
        assertInstanceOf(ProjectionResult.Rejected.class, registered(ProjectionOperation.SUCCESSION_FREEZE)
                .execute(call(ProjectionOperation.SUCCESSION_FREEZE, original.getBytes(StandardCharsets.UTF_8))));
    }
    @Test void knownFreezeRefusalIsDomainAndUnrelatedProjectFailureStaysTechnical() throws IOException {
        ObjectNode request = (ObjectNode) StreamSupport.stream(golden().get("cases").spliterator(), false)
                .map(row -> row.get("request")).filter(row -> row.get("operation").textValue().equals("freeze")).findFirst().orElseThrow().deepCopy();
        request.put("episode_character_id", request.get("episode_character_id").intValue() + 1);
        ProjectionResult.Rejected refusal = assertInstanceOf(ProjectionResult.Rejected.class,
                registered(ProjectionOperation.SUCCESSION_FREEZE).execute(call(ProjectionOperation.SUCCESSION_FREEZE, SuccessionCodec.encode(request))));
        assertEquals(ProjectionError.Code.DOMAIN_REJECTED, refusal.error().code());
        var failing = RegisteredProjection.of(new ProjectionPort<byte[], byte[]>() {
            @Override public ProjectionOperation operation() { return ProjectionOperation.SUCCESSION_FREEZE; }
            @Override public byte[] decode(byte[] payload) { return payload; }
            @Override public byte[] project(byte[] input) { throw new IllegalArgumentException("injected internal programming failure"); }
            @Override public byte[] encode(byte[] output) { return output; }
        });
        ProjectionResult.Rejected technical = assertInstanceOf(ProjectionResult.Rejected.class,
                failing.execute(call(ProjectionOperation.SUCCESSION_FREEZE, "{}".getBytes(StandardCharsets.UTF_8))));
        assertEquals(ProjectionError.Code.PROJECTION_FAILED, technical.error().code());
    }
    private static ProjectionOperation operation(String wire) {
        return switch (wire) { case "freeze" -> ProjectionOperation.SUCCESSION_FREEZE; case "normalize" -> ProjectionOperation.SUCCESSION_NORMALIZE; case "reconcile" -> ProjectionOperation.SUCCESSION_RECONCILE; default -> throw new IllegalArgumentException(wire); };
    }
    private static RegisteredProjection registered(ProjectionOperation operation) { return new SuccessionProjectionCatalog().registrations().stream().filter(port -> port.operation() == operation).findFirst().orElseThrow(); }
    private static ProjectionCall call(ProjectionOperation operation, byte[] payload) { return new ProjectionCall(new ProjectionCall.Identity("succession-original-consumer-fixture", operation), ProjectionJson.object(payload, 131_072)); }
    private static JsonNode golden() throws IOException {
        try (var input = SuccessionProjectionCatalogTest.class.getResourceAsStream("/succession/original-producer-golden.json")) {
            assertNotNull(input, "actual original producer and consumer golden is mandatory"); return SuccessionCodec.parse(input.readAllBytes());
        }
    }
}
