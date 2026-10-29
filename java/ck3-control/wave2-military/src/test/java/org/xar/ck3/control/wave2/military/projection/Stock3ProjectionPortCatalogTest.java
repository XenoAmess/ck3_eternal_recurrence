package org.xar.ck3.control.wave2.military.projection;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.ServiceLoader;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.projection.ProjectionCall;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionResult;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

final class Stock3ProjectionPortCatalogTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);
    private static final List<ProjectionOperation> OPERATIONS = List.of(
            ProjectionOperation.MILITARY_UPDATER_WRITES, ProjectionOperation.MILITARY_STOCK_SUPPLY,
            ProjectionOperation.MILITARY_NEXT_FLEET_RATE, ProjectionOperation.MILITARY_CALLBACK_SUPPLY_RISK,
            ProjectionOperation.MILITARY_CALLBACK_SOLDIER_EFFECTS);

    @Test void realServiceLoaderDiscoversFiveDistinctTypedPortsAndFiniteProfiles() {
        assertEquals(5, ports().size());
        assertEquals(5, ports().stream().map(RegisteredProjection::operation).distinct().count());
        for (ProjectionOperation operation : OPERATIONS) {
            assertEquals(65_536, port(operation).inputMaximumBytes());
            assertEquals(65_536, port(operation).outputMaximumBytes());
        }
    }

    @Test void everyOriginalProducerVectorCrossesTheRegisteredTypedPort() throws IOException {
        JsonNode updater = golden("/updaterwrites/source-next-updater-golden-v1.json.gz");
        assertEquals(24, updater.path("projections").size());
        compare(updater.path("projections"), "expected", ProjectionOperation.MILITARY_UPDATER_WRITES);
        JsonNode stock = golden("/stocksupply/original-stock-supply-golden-v1.json.gz");
        assertEquals(10, stock.path("vectors").size());
        assertEquals(12, stock.path("rate_vectors").size());
        compare(stock.path("vectors"), "expected", ProjectionOperation.MILITARY_STOCK_SUPPLY);
        compare(stock.path("rate_vectors"), "expected", ProjectionOperation.MILITARY_NEXT_FLEET_RATE);
        JsonNode callback = golden("/callbackrisk/original-callback-risk-golden-v1.json.gz");
        assertEquals(8, callback.path("vectors").size());
        compare(callback.path("vectors"), "expected_risk", ProjectionOperation.MILITARY_CALLBACK_SUPPLY_RISK);
        for (JsonNode vector : callback.path("vectors")) {
            var payload = JSON.createObjectNode();
            payload.set("army", effectsRow(vector.get("input")));
            payload.set("callback_risk", effectsRisk(vector.get("expected_risk")));
            assertEquals(vector.get("expected_effects"), result(ProjectionOperation.MILITARY_CALLBACK_SOLDIER_EFFECTS,
                    JSON.writeValueAsBytes(payload)));
        }
    }

    @Test void rawBooleanFloatExponentStringAndOverflowIdentityTokensRemainRejected() {
        for (ProjectionOperation operation : OPERATIONS.subList(0, 4)) {
            for (String token : List.of("true", "1.0", "1e0", "\"1\"", "2147483648")) {
                byte[] raw = ("{\"status\":\"available\",\"army_id\":" + token + ",\"native_carmy_id\":0}").getBytes(StandardCharsets.UTF_8);
                ProjectionResult.Rejected rejected = assertInstanceOf(ProjectionResult.Rejected.class, execute(operation, raw));
                assertEquals(ProjectionError.Code.INVALID_PAYLOAD, rejected.error().code());
            }
        }
    }

    @Test void externalBudgetIsConsumedWithoutRecomputingRiskAndWrongTokensFail() throws IOException {
        JsonNode vector = golden("/callbackrisk/original-callback-risk-golden-v1.json.gz").path("vectors").get(0);
        for (int budget : List.of(0, 2)) {
            var payload = JSON.createObjectNode();
            payload.set("army", effectsRow(vector.get("input")));
            var risk = (com.fasterxml.jackson.databind.node.ObjectNode) effectsRisk(vector.get("expected_risk"));
            risk.put("conditional_supply_budget_soldiers", budget);
            payload.set("callback_risk", risk);
            JsonNode output = result(ProjectionOperation.MILITARY_CALLBACK_SOLDIER_EFFECTS, JSON.writeValueAsBytes(payload));
            assertEquals(budget, output.path("conditional_supply_budget_soldiers").intValue());
            assertEquals(101 - budget, output.path("conditional_loss_sequence_v1").path("conditional_final_current_soldiers").intValue());
        }
        for (String token : List.of("true", "1.0", "1e0", "\"1\"", "2147483648")) {
            byte[] raw = ("{\"army\":{\"status\":\"available\"},\"callback_risk\":"
                    + "{\"conditional_supply_budget_ready\":true,\"conditional_supply_budget_soldiers\":" + token + "}}")
                    .getBytes(StandardCharsets.UTF_8);
            var rejected = assertInstanceOf(ProjectionResult.Rejected.class,
                    execute(ProjectionOperation.MILITARY_CALLBACK_SOLDIER_EFFECTS, raw));
            assertEquals(ProjectionError.Code.INVALID_PAYLOAD, rejected.error().code());
        }
        var payload = JSON.createObjectNode();
        payload.set("army", effectsRow(vector.get("input")));
        var wrong = (com.fasterxml.jackson.databind.node.ObjectNode) effectsRisk(vector.get("expected_risk"));
        wrong.put("unexpected_budget_alias", 2); payload.set("callback_risk", wrong);
        assertInstanceOf(ProjectionResult.Rejected.class,
                execute(ProjectionOperation.MILITARY_CALLBACK_SOLDIER_EFFECTS, JSON.writeValueAsBytes(payload)));
    }

    private static JsonNode effectsRow(JsonNode row) {
        var result = JSON.createObjectNode();
        for (String field : List.of("status", "army_id", "native_carmy_id", "current_soldiers",
                "loss_application_inputs_v1", "regiment_strengths", "regiment_replenishment_records_v1")) {
            if (row.has(field)) result.set(field, row.get(field));
        }
        return result;
    }
    private static JsonNode effectsRisk(JsonNode risk) {
        var result = JSON.createObjectNode();
        for (String field : List.of("conditional_supply_budget_ready", "conditional_supply_budget_soldiers",
                "conditional_post_stock_ready", "conditional_post_stock_raw")) {
            if (risk.has(field)) result.set(field, risk.get(field));
        }
        return result;
    }
    private static void compare(JsonNode vectors, String expected, ProjectionOperation operation) throws IOException {
        for (JsonNode vector : vectors) {
            byte[] raw = JSON.writeValueAsBytes(vector.get("input"));
            assertEquals(vector.get(expected), result(operation, raw), operation.wire() + ":" + vector.path("id").asText());
            assertEquals(vector.get("input"), JSON.readTree(raw));
        }
    }
    private static List<RegisteredProjection> ports() {
        List<ProjectionPortCatalog> matches = ServiceLoader.load(ProjectionPortCatalog.class).stream()
                .filter(provider -> provider.type().equals(MilitaryProjectionPortCatalog.class)).map(ServiceLoader.Provider::get).toList();
        assertEquals(1, matches.size(), "actual module SPI resource must register this catalog once");
        return matches.getFirst().registrations().stream().filter(value -> OPERATIONS.contains(value.operation())).toList();
    }
    private static RegisteredProjection port(ProjectionOperation operation) {
        return ports().stream().filter(value -> value.operation() == operation).findFirst().orElseThrow();
    }
    private static ProjectionResult execute(ProjectionOperation operation, byte[] raw) {
        ProjectionCall.Identity identity = new ProjectionCall.Identity("stock3-port-contract", operation);
        ProjectionResult value = port(operation).execute(new ProjectionCall(identity, ProjectionJson.object(raw, ProjectionJson.MAX_BYTES)));
        if (value instanceof ProjectionResult.Succeeded success) assertEquals(identity, success.identity());
        if (value instanceof ProjectionResult.Rejected rejected) assertEquals(identity, rejected.identity().orElseThrow());
        return value;
    }
    private static JsonNode result(ProjectionOperation operation, byte[] raw) throws IOException {
        return JSON.readTree(assertInstanceOf(ProjectionResult.Succeeded.class, execute(operation, raw)).result().bytes());
    }
    private static JsonNode golden(String name) throws IOException {
        try (var input = Stock3ProjectionPortCatalogTest.class.getResourceAsStream(name)) {
            if (input == null) throw new IOException("fresh qualified producer gzip required: " + name);
            byte[] compressed = input.readNBytes(16_385);
            if (compressed.length == 0 || compressed.length > 16_384) throw new IOException("compressed golden exceeds finite budget");
            try (var gzip = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
                byte[] raw = gzip.readNBytes(131_073);
                if (raw.length == 0 || raw.length > 131_072) throw new IOException("raw golden exceeds finite budget");
                StandardCharsets.UTF_8.newDecoder().decode(ByteBuffer.wrap(raw));
                return JSON.readTree(raw);
            }
        }
    }
}
