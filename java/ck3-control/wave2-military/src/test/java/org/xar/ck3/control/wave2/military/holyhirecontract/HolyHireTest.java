package org.xar.ck3.control.wave2.military.holyhirecontract;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import static org.junit.jupiter.api.Assertions.*;

final class HolyHireTest {
    private static final int BUDGET = 131_072;
    private static JsonNode golden() throws IOException {
        try (var resource = HolyHireTest.class.getResourceAsStream("/holyhirecontract/golden.json.gz")) {
            assertNotNull(resource, "unified execution owner must capture actual original producer; absent golden is a failure");
            try (var gzip = new GZIPInputStream(resource)) {
                JsonNode data = StrictJson.parse(gzip.readNBytes(262_145), 262_144);
                assertEquals("xar.ck3.holy-hire-contract-golden.v1", data.path("schema").asText());
                assertFalse(data.path("machine_id").asText().isBlank()); assertNotEquals("unknown", data.path("machine_id").asText());
                assertTrue(data.path("actual_original_normalizers").booleanValue()); assertTrue(data.path("actual_private_query_helper").booleanValue());
                assertTrue(data.path("synthetic_transport_callbacks").booleanValue()); assertEquals(0, data.path("game_operations").intValue());
                assertTrue(data.path("source_pins").size() >= 10); return data;
            }
        }
    }
    @TestFactory List<DynamicTest> originalRequestAckAndPrivateQueryDifferential() throws IOException {
        List<DynamicTest> cases = new ArrayList<>();
        for (JsonNode row : golden().path("cases")) {
            cases.add(DynamicTest.dynamicTest(row.path("name").asText(), () -> {
                byte[] raw = StrictJson.canonical(row.get("input"), BUDGET);
                if (!row.path("accepted").booleanValue()) { assertThrows(IllegalArgumentException.class, () -> execute(row.path("operation").asText(), raw)); }
                else {
                    JsonNode actual = execute(row.path("operation").asText(), raw); assertEquals(row.get("expected"), actual);
                    assertEquals(actual, StrictJson.parse(StrictJson.canonical(actual, BUDGET), BUDGET));
                    if (row.path("operation").asText().equals("ack")) { assertFalse(actual.path("holy_order_hire").path("after_state_observed").booleanValue()); }
                }
            }));
        }
        assertTrue(cases.size() >= 25); return cases;
    }
    private static JsonNode execute(String operation, byte[] raw) {
        return switch (operation) {
            case "ack" -> StrictJson.parse(HolyHireCodec.acknowledge(raw), BUDGET);
            case "query" -> StrictJson.parse(HolyHireCodec.query(raw), BUDGET);
            case "request" -> {
                HolyHireContract.Request request = HolyHireCodec.request(raw);
                ObjectNode encoded = StrictJson.object().put("holy_order_id", request.holyOrderId()).put("expected_revision", request.expectedRevision());
                // Request is a domain record; use the same strict serialized JSON domain
                // as ACK/query adapters and the captured original producer.
                yield StrictJson.parse(StrictJson.canonical(encoded, BUDGET), BUDGET);
            }
            default -> throw new IllegalArgumentException("unknown capture operation");
        };
    }
    private static ObjectNode sample(String name) throws IOException {
        for (JsonNode row : golden().path("cases")) { if (row.path("name").asText().equals(name)) { return (ObjectNode) row.get("input").deepCopy(); } }
        throw new IllegalArgumentException("sample absent: " + name);
    }
    @Test void rejectsRawFloatBoolAndStringRevisionWithoutNumberCoercion() {
        for (String token : List.of("1.0", "true", "\"1\"", "-1")) {
            String raw = "{\"schema\":\"" + HolyHireCodec.REQUEST_SCHEMA + "\",\"holy_order_id\":0,\"expected_revision\":" + token + "}";
            assertThrows(IllegalArgumentException.class, () -> HolyHireCodec.request(raw.getBytes(StandardCharsets.UTF_8)));
        }
    }
    @Test void queryBindingIncludesBlockerScopeAndFullSource() throws IOException {
        ObjectNode input = sample("query-normalized-current-context");
        ((ObjectNode) input.get("after_snapshot")).putObject("active_event").put("instance_id", "new");
        byte[] crossedScope = StrictJson.canonical(input, BUDGET);
        assertThrows(IllegalArgumentException.class, () -> HolyHireCodec.query(crossedScope));
        input = sample("query-normalized-current-context"); ((ObjectNode) input.get("packet")).put("ok", false);
        byte[] raw = StrictJson.canonical(input, BUDGET); assertThrows(IllegalArgumentException.class, () -> HolyHireCodec.query(raw));
    }
    @Test void nativeDriverAdapterRequiresActualExpectedPublicRevision() throws IOException {
        ObjectNode input = sample("native-driver-submitted-binding"); input.put("expected_revision", 11);
        assertThrows(IllegalArgumentException.class, () -> HolyHireCodec.acknowledge(StrictJson.canonical(input, BUDGET)));
    }
}
