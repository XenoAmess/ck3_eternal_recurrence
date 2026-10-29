package org.xar.ck3.control.wave3.military.landcontext;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ServiceLoader;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.projection.*;

final class LandContextProjectionCatalogTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
    private static RegisteredProjection port() {
        var catalogs = ServiceLoader.load(ProjectionPortCatalog.class).stream()
                .filter(value -> value.type().equals(LandContextProjectionCatalog.class)).map(ServiceLoader.Provider::get).toList();
        assertEquals(1, catalogs.size());
        var registrations = catalogs.getFirst().registrations();
        assertEquals(2, registrations.size());
        assertEquals(Set.of(ProjectionOperation.MILITARY_LAND_CONTEXT_STOCK,
                ProjectionOperation.MILITARY_HOLY_DEFENDER_OBSERVATION),
                Set.copyOf(registrations.stream().map(RegisteredProjection::operation).toList()));
        var land = registrations.stream()
                .filter(value -> value.operation() == ProjectionOperation.MILITARY_LAND_CONTEXT_STOCK).toList();
        assertEquals(1, land.size());
        return land.getFirst();
    }
    @Test void actualSpiHasOneTypedOperationWithExplicitBounds() {
        assertEquals(ProjectionOperation.MILITARY_LAND_CONTEXT_STOCK, port().operation());
        assertEquals(524_288, port().inputMaximumBytes()); assertEquals(524_288, port().outputMaximumBytes());
    }
    @Test void everyOriginalWholeStockVectorCrossesRegisteredTypedApplication() throws IOException {
        JsonNode golden;
        try (var stream = getClass().getResourceAsStream("/landcontext/full-land-context-golden-v1.json")) {
            if (stream == null) throw new IOException("original complete producer golden required; no fallback");
            byte[] raw = stream.readNBytes(1_048_577);
            assertTrue(raw.length > 0 && raw.length <= 1_048_576); golden = JSON.readTree(raw);
        }
        assertTrue(golden.path("stocks").size() >= 7);
        for (JsonNode vector : golden.path("stocks")) {
            ObjectNode row = merge(golden.path("base_row").deepCopy(), vector.path("patch"));
            byte[] raw = JSON.writeValueAsBytes(row);
            var success = assertInstanceOf(ProjectionResult.Succeeded.class, execute(raw));
            assertEquals(vector.get("expected"), JSON.readTree(success.result().bytes()));
            assertEquals(row, JSON.readTree(raw));
        }
    }
    @Test void originalIntegerTokenKindsStayRejectedAtTheRegisteredBoundary() {
        for (String token : java.util.List.of("true", "1.0", "1e0", "\"1\"", "2147483648")) {
            byte[] raw = ("{\"army_id\":" + token + "}").getBytes(StandardCharsets.UTF_8);
            assertInstanceOf(ProjectionResult.Rejected.class, execute(raw));
        }
    }
    private static ProjectionResult execute(byte[] raw) {
        var identity = new ProjectionCall.Identity("land-context-stock-regression", ProjectionOperation.MILITARY_LAND_CONTEXT_STOCK);
        return port().execute(new ProjectionCall(identity, ProjectionJson.object(raw, ProjectionJson.MAX_BYTES)));
    }
    private static ObjectNode merge(ObjectNode target, JsonNode patch) {
        patch.properties().forEach(property -> {
            JsonNode current = target.get(property.getKey()), value = property.getValue();
            if (value.isObject() && current != null && current.isObject()) merge((ObjectNode) current, value);
            else target.set(property.getKey(), value.deepCopy());
        });
        return target;
    }
}
