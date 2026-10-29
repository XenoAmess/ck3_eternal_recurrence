package org.xar.ck3.control.wave2.military.coalitionreceipt;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.coalitionreceipt.CoalitionExecutionReceipt.ValidatedCommandResult;

final class CoalitionExecutionReceiptTest {
    @Test
    void unchangedOriginalTransportAndHistorySummaryGolden() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.coalitionreceipt.original-producer-golden/v1", golden.path("schema").textValue());
        int summaries = 0;
        int receiptOnly = 0;
        int rejected = 0;
        for (JsonNode sample : golden.path("cases")) {
            ObjectNode request = golden.path("base").deepCopy();
            for (JsonNode edit : sample.path("edits")) apply(request, edit);
            ObjectNode untouched = request.deepCopy();
            JsonNode expected = sample.path("expected");
            String id = sample.path("id").textValue();
            if (!expected.path("accepted").booleanValue()) {
                assertThrows(IllegalArgumentException.class, () -> evaluate(request, sample.path("summary").booleanValue()), id);
                rejected++;
            } else {
                ValidatedCommandResult command = CoalitionExecutionReceipt.validate(request.get("frame"), request.get("expected_request_id").textValue());
                assertEquals(canonical(expected.get("receipt")), canonical(command.receipt().toJson()), id);
                assertEquals(expected.path("status").textValue(), command.status().wire(), id);
                JsonNode originalBody = request.path("frame").path("result").get(CoalitionExecutionReceipt.DOMAIN_KEY);
                assertEquals(originalBody, command.unvalidatedBodyCopy(), "body token preservation: " + id);
                if (sample.path("summary").booleanValue()) {
                    ObjectNode result = evaluate(request, true);
                    assertEquals(canonical(expected.get("summary")), canonical(result), id);
                    assertFalse(result.path("full_result_preserved").booleanValue());
                    assertFalse(result.has(CoalitionExecutionReceipt.DOMAIN_KEY));
                    summaries++;
                } else receiptOnly++;
                JsonNode exportedBody = command.unvalidatedBodyCopy();
                if (exportedBody instanceof ObjectNode object) object.put("mutated", true);
                assertEquals(originalBody, command.unvalidatedBodyCopy(), "detached body: " + id);
            }
            assertEquals(untouched, request, "transport boundary mutated input: " + id);
        }
        assertTrue(summaries >= 2); assertTrue(receiptOnly >= 5); assertTrue(rejected >= 40);
    }

    @Test
    void summaryCannotBeReusedAsFullCommandResult() throws IOException {
        ObjectNode request = golden().path("base").deepCopy();
        ObjectNode summary = evaluate(request, true);
        assertThrows(IllegalArgumentException.class, () -> CoalitionExecutionReceipt.validate(summary, request.get("expected_request_id").textValue()));
        assertThrows(IllegalArgumentException.class, () -> CoalitionExecutionReceipt.validate(
                StrictJson.parse("{\"type\":\"command_result\",\"type\":\"command_result\"}".getBytes(StandardCharsets.UTF_8)), "fresh"));
    }

    @Test
    void actualExportedTopBindingFeedsRealCoalitionWithoutDomainTicketSubstitution() throws IOException {
        ObjectNode request = golden().path("base").deepCopy();
        ValidatedCommandResult command = CoalitionExecutionReceipt.validate(request.get("frame"), request.get("expected_request_id").textValue());
        assertEquals(command.requestId(), command.exportIndependentBinding().path("request_id").textValue());
        var current = CoalitionExecutionReceipt.normalizeAgainstLease(command, request.get("snapshot"), request.get("declaration"), null);
        assertEquals(1500L, current.observation().actorLowerSoldiers());
        ObjectNode encoded = command.commandResultJson();
        ValidatedCommandResult roundTrip = CoalitionExecutionReceipt.validate(StrictJson.parse(StrictJson.canonical(encoded)), command.requestId());
        assertEquals(command.receipt(), roundTrip.receipt());
        assertEquals(canonical(CoalitionExecutionReceipt.historySummary(current)), canonical(CoalitionExecutionReceipt.historySummary(
                CoalitionExecutionReceipt.normalizeAgainstLease(roundTrip, request.get("snapshot"), request.get("declaration"), null))));
    }

    private static ObjectNode evaluate(ObjectNode request, boolean summary) {
        ValidatedCommandResult command = CoalitionExecutionReceipt.validate(request.get("frame"), request.get("expected_request_id").textValue());
        if (!summary) return command.receipt().toJson();
        return CoalitionExecutionReceipt.historySummary(CoalitionExecutionReceipt.normalizeAgainstLease(command, request.get("snapshot"), request.get("declaration"), null));
    }
    private static JsonNode golden() throws IOException {
        try (InputStream input = CoalitionExecutionReceiptTest.class.getResourceAsStream("/coalitionreceipt/original-producer-golden01.json")) {
            assertNotNull(input, "committed actual producer golden required");
            return StrictJson.parse(input.readAllBytes(), 51_200);
        }
    }
    private static String canonical(JsonNode value) { return new String(StrictJson.canonical(value), StandardCharsets.UTF_8); }
    private static void apply(ObjectNode request, JsonNode edit) {
        JsonNode path = edit.get("path"); JsonNode parent = request;
        for (int i = 0; i < path.size() - 1; i++) {
            JsonNode key = path.get(i); parent = key.isTextual() ? parent.get(key.textValue()) : parent.get(key.intValue());
        }
        JsonNode key = path.get(path.size() - 1);
        if (edit.path("remove").asBoolean()) {
            if (parent instanceof ObjectNode object) object.remove(key.textValue()); else ((ArrayNode) parent).remove(key.intValue());
        } else {
            JsonNode value = StrictJson.parse(edit.get("value_json").textValue().getBytes(StandardCharsets.UTF_8));
            if (parent instanceof ObjectNode object) object.set(key.textValue(), value); else ((ArrayNode) parent).set(key.intValue(), value);
        }
    }
}
