package org.xar.ck3.control.wave3.military.landcontext;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.projection.*;
import org.xar.ck3.control.wave2.military.projection.MilitaryProjectionPortCatalog;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyCodec;
import org.xar.ck3.control.wave2.military.fleetsupply.FleetSupplyProjection;

final class StockAndLandHost04RejectionTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static RegisteredProjection stock(ProjectionOperation operation) {
        return new MilitaryProjectionPortCatalog().registrations().stream()
                .filter(port -> port.operation() == operation).findFirst().orElseThrow();
    }
    private static RegisteredProjection land() { return new LandContextProjectionCatalog().registrations().getFirst(); }

    @Test void rawTokenErrorsStayInvalidPayloadBeforeProject() throws IOException {
        ObjectNode row = JSON.createObjectNode(); row.put("army_id", true);
        for (RegisteredProjection port : List.of(stock(ProjectionOperation.MILITARY_STOCK_SUPPLY),
                stock(ProjectionOperation.MILITARY_NEXT_FLEET_RATE), land())) {
            expect(port, row, ProjectionError.Code.INVALID_PAYLOAD);
        }
    }
    @Test void actualSameQueryGuardsRemainExplicitDomainRefusals() throws IOException {
        JsonNode original = golden("/stocksupply/original-stock-supply-golden-v1.json.gz", true)
                .path("vectors").get(0).get("input");
        for (String id : List.of("subject_army_id", "subject_carmy_id")) {
            ObjectNode row = original.deepCopy();
            ((ObjectNode) row.get("current_fleet_supply_tick_inputs_v1")).put(id, 99);
            expect(stock(ProjectionOperation.MILITARY_NEXT_FLEET_RATE), row, ProjectionError.Code.DOMAIN_REJECTED);
            assertThrows(ProjectionDomainRejection.class,
                    () -> FleetSupplyProjection.project(FleetSupplyCodec.decodeRow(row)));
        }
        ObjectNode wrongClock = original.deepCopy();
        ObjectNode tick = (ObjectNode) wrongClock.get("current_fleet_supply_tick_inputs_v1");
        tick.put("current_native_date_low32", tick.path("current_native_date_low32").intValue() + 1);
        expect(stock(ProjectionOperation.MILITARY_STOCK_SUPPLY), wrongClock, ProjectionError.Code.DOMAIN_REJECTED);
        JsonNode base = golden("/landcontext/full-land-context-golden-v1.json", false).path("base_row");
        for (String field : List.of("province_id", "owner_character_id", "subject_army_id", "subject_carmy_id")) {
            ObjectNode row = base.deepCopy();
            ObjectNode province = (ObjectNode) row.get("current_province_supply_contributors_v1");
            province.put(field, province.path(field).intValue() + 1);
            expect(land(), row, ProjectionError.Code.DOMAIN_REJECTED);
        }
    }
    @Test void injectedAlgorithmAndFormatterBugsStayInternalAndAreNotDomainRefusals() throws IOException {
        // These two test-only sentinels check the framework boundary, not an observed production bug.
        for (boolean formatter : List.of(false, true)) {
            var port = RegisteredProjection.of(new ProjectionPort<Integer, Integer>() {
                public ProjectionOperation operation() { return ProjectionOperation.MILITARY_STOCK_SUPPLY; }
                public Integer decode(byte[] raw) { return 1; }
                public Integer project(Integer input) {
                    if (!formatter) throw new IllegalArgumentException("injected algorithm bug");
                    return input;
                }
                public byte[] encode(Integer output) { throw new IllegalArgumentException("injected formatter bug"); }
            });
            expect(port, JSON.createObjectNode(), formatter ? ProjectionError.Code.INVALID_RESULT : ProjectionError.Code.PROJECTION_FAILED);
        }
    }
    private static void expect(RegisteredProjection port, JsonNode row, ProjectionError.Code code) throws IOException {
        var identity = new ProjectionCall.Identity("stock-land-host04-negative", port.operation());
        var result = port.execute(new ProjectionCall(identity, ProjectionJson.object(JSON.writeValueAsBytes(row), ProjectionJson.MAX_BYTES)));
        var rejected = assertInstanceOf(ProjectionResult.Rejected.class, result);
        assertEquals(identity, rejected.identity().orElseThrow()); assertEquals(code, rejected.error().code());
    }
    private static JsonNode golden(String name, boolean gzip) throws IOException {
        try (var stream = StockAndLandHost04RejectionTest.class.getResourceAsStream(name)) {
            if (stream == null) throw new IOException("original producer evidence required: " + name);
            if (gzip) {
                byte[] compressed = stream.readNBytes(16_385);
                assertTrue(compressed.length > 0 && compressed.length <= 16_384);
                try (var expanded = new GZIPInputStream(new java.io.ByteArrayInputStream(compressed))) {
                    byte[] raw = expanded.readNBytes(131_073);
                    assertTrue(raw.length > 0 && raw.length <= 131_072); return JSON.readTree(raw);
                }
            }
            byte[] raw = stream.readNBytes(1_048_577);
            assertTrue(raw.length > 0 && raw.length <= 1_048_576); return JSON.readTree(raw);
        }
    }
}
