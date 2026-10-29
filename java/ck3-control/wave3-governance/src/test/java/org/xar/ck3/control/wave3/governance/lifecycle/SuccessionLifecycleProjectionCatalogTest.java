package org.xar.ck3.control.wave3.governance.lifecycle;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.List;
import java.util.ServiceLoader;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.projection.*;
import static org.junit.jupiter.api.Assertions.*;

final class SuccessionLifecycleProjectionCatalogTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    @TestFactory Stream<DynamicTest> originalLifecycleProducersThroughRegisteredPorts() throws IOException {
        return StreamSupport.stream(golden().get("cases").spliterator(), false).map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
            JsonNode request = row.get("request"); ProjectionOperation operation = request.get("operation").textValue().equals("normalize") ? ProjectionOperation.LIFECYCLE_NORMALIZE : ProjectionOperation.LIFECYCLE_CONSTRUCT;
            ProjectionResult.Succeeded result = assertInstanceOf(ProjectionResult.Succeeded.class, execute(operation, request));
            assertEquals(row.get("expected"), JSON.readTree(result.result().bytes()));
        }));
    }
    @TestFactory Stream<DynamicTest> actualOriginalThreeAnchorConsumersThroughTheRegisteredPort() throws IOException {
        JsonNode source = golden(); assertEquals(20, source.get("anchor_consumer_cases").size());
        return StreamSupport.stream(source.get("anchor_consumer_cases").spliterator(), false).flatMap(row ->
                List.of("checkpoint", "ordinary", "rogue").stream().map(consumer -> DynamicTest.dynamicTest(row.get("name").textValue() + ":" + consumer, () -> {
                    ObjectNode request = JSON.createObjectNode().put("schema", SuccessionLifecycleConsumerPort.SCHEMA).put("operation", consumer + "_anchors");
                    request.set("driver", row.get("anchors").get(0)); request.set("checkpoint", row.get("anchors").get(1)); request.set("saved_history", row.get("anchors").get(2));
                    String key = consumer.equals("checkpoint") ? "checkpoint_environment_binding" : consumer + (consumer.equals("ordinary") ? "_seed_anchors" : "_checkpoint_anchors");
                    JsonNode expected = row.get("actual_consumers").get(key); ProjectionResult result = execute(ProjectionOperation.LIFECYCLE_THREE_ANCHOR, request);
                    if (expected.get("accepted").booleanValue()) {
                        assertEquals(expected.get("binding"), JSON.readTree(assertInstanceOf(ProjectionResult.Succeeded.class, result).result().bytes()));
                    } else { assertInstanceOf(ProjectionResult.Rejected.class, result); }
                })));
    }
    @Test void serviceDescriptorAndOriginalLeafBudgetAreRetained() {
        assertTrue(ServiceLoader.load(ProjectionPortCatalog.class).stream().anyMatch(provider -> provider.type().equals(SuccessionLifecycleProjectionCatalog.class)));
        assertEquals(4, new SuccessionLifecycleProjectionCatalog().registrations().size());
        var port = new SuccessionLifecycleProjectionCatalog.AnchorPort();
        assertEquals(16_384, port.inputMaximumBytes()); assertEquals(16_384, port.outputMaximumBytes());
    }
    @Test void knownProfileRefusalRemainsDomainAfterTypedDecode() {
        ObjectNode request = JSON.createObjectNode().put("schema", SuccessionLifecycleConsumerPort.SCHEMA).put("operation", "ordinary_seed");
        request.set("binding", SuccessionLifecycleCodec.parse(SuccessionLifecycleCodec.encode(SuccessionLifecycleBinding.legacyRogue())));
        ProjectionResult.Rejected refusal = assertInstanceOf(ProjectionResult.Rejected.class, execute(ProjectionOperation.LIFECYCLE_CONSUMER, request));
        assertEquals(ProjectionError.Code.DOMAIN_REJECTED, refusal.error().code());
    }
    private static ProjectionResult execute(ProjectionOperation operation, JsonNode request) {
        ProjectionCall call = new ProjectionCall(new ProjectionCall.Identity("lifecycle-original-consumer-fixture", operation), ProjectionJson.object(SuccessionLifecycleCodec.encodeNode(request), 16_384));
        return new SuccessionLifecycleProjectionCatalog().registrations().stream().filter(port -> port.operation() == operation).findFirst().orElseThrow().execute(call);
    }
    private static JsonNode golden() throws IOException {
        try (var input = SuccessionLifecycleProjectionCatalogTest.class.getResourceAsStream("/lifecycle/original-producer-golden.json")) {
            assertNotNull(input, "actual original producer/three-reader golden is mandatory"); byte[] bytes = input.readNBytes(60_001); assertTrue(bytes.length <= 60_000); return JSON.readTree(bytes);
        }
    }
}
