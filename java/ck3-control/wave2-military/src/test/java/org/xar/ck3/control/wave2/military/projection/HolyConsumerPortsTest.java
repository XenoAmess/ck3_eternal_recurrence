package org.xar.ck3.control.wave2.military.projection;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.io.ByteArrayInputStream;
import java.util.Map;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.*;
import org.xar.ck3.control.wave2.military.holyreinf.HolyReinforcementCodec;
import static org.junit.jupiter.api.Assertions.*;

final class HolyConsumerPortsTest {
    private static byte[] raw(String s) { return s.getBytes(StandardCharsets.UTF_8); }
    private static JsonNode golden(String leaf) throws Exception {
        try (var stream = HolyConsumerPortsTest.class.getResourceAsStream("/" + leaf + "/golden.json.gz")) {
            assertNotNull(stream, "original oracle remains mandatory");
            byte[] compressed = stream.readNBytes(65537); assertTrue(compressed.length <= 65536, "64 KiB compressed fixture cap");
            try (var gzip = new GZIPInputStream(new ByteArrayInputStream(compressed))) {
                return StrictJson.parse(gzip.readNBytes(262145), 262144);
            }
        }
    }
    private static ProjectionResult call(boolean hire, String op, String stage, JsonNode req) {
        ObjectNode packet = StrictJson.object().put("operation", op); packet.set("request", req);
        if (stage != null) { packet.put("stage", stage); }
        return callRaw(hire, StrictJson.canonical(packet, 131072));
    }
    private static ProjectionResult callRaw(boolean hire, byte[] originalPayload) {
        var operation = hire ? ProjectionOperation.MILITARY_HOLY_HIRE : ProjectionOperation.MILITARY_HOLY_REINFORCEMENT;
        var ports = HolyConsumerPorts.registrations(new HolyConsumerPorts.Operations(
                ProjectionOperation.MILITARY_HOLY_REINFORCEMENT, ProjectionOperation.MILITARY_HOLY_HIRE));
        var input = new ProjectionCall(new ProjectionCall.Identity("holy-original-regression", operation),
                ProjectionJson.object(originalPayload, 131072));
        return ports.get(hire ? 1 : 0).execute(input);
    }
    @Test void completeOriginalHireOracleCrossesTheActualRegisteredPort() throws Exception {
        int count = 0;
        for (JsonNode row : golden("holyhirecontract").get("cases")) {
            count++; String op = row.get("operation").textValue();
            var result = call(true, op, op.equals("query") ? "envelope" : null, row.get("input"));
            if (!row.get("accepted").booleanValue()) { assertInstanceOf(ProjectionResult.Rejected.class, result); }
            else {
                byte[] actual = assertInstanceOf(ProjectionResult.Succeeded.class, result).result().bytes();
                assertEquals(op.equals("request") ? StrictJson.object().nullNode() : row.get("expected"), StrictJson.parse(actual, 131072));
            }
        }
        assertTrue(count >= 25);
    }
    @Test void completeOriginalReinforcementOracleIncludesTheRealSelectedProposalSeam() throws Exception {
        int count = 0;
        for (JsonNode row : golden("holyreinf").get("cases")) {
            count++; String op = row.get("operation").textValue(); JsonNode input = row.get("input"); String stage = null;
            if (op.equals("post")) {
                ObjectNode choose = StrictJson.object().put("schema", HolyReinforcementCodec.CHOOSE_SCHEMA);
                choose.set("snapshot", input.get("before_snapshot")); choose.set("plan", input.get("plan"));
                choose.set("holy_context", input.get("before_context"));
                ObjectNode selected = StrictJson.object().put("schema", HolyReinforcementCodec.SELECTED_POST_SCHEMA);
                selected.set("proposal", HolyReinforcementCodec.chooseNode(StrictJson.canonical(choose, 131072)));
                for (String field : new String[]{"ack", "after_snapshot", "after_context", "army_strengths",
                        "actor_expenses", "expense_query_error", "post_query_error"}) { selected.set(field, input.get(field)); }
                input = selected; op = "postcondition"; stage = "fold";
            } else if (op.equals("plan")) { stage = "fold"; }
            byte[] actual = assertInstanceOf(ProjectionResult.Succeeded.class, call(false, op, stage, input)).result().bytes();
            assertEquals(row.get("expected"), StrictJson.parse(actual, 131072), row.get("name").textValue());
            if (row.get("name").textValue().equals("ack-and-independent-material-army")) {
                ObjectNode partial = input.deepCopy(); partial.put("post_query_error", "");
                byte[] partialRaw = assertInstanceOf(ProjectionResult.Succeeded.class,
                        call(false, "postcondition", "fold", partial)).result().bytes();
                JsonNode receipt = StrictJson.parse(partialRaw, 131072).get("holy_order_reinforcement_postcondition");
                assertEquals("verification_pending", receipt.get("status").textValue());
                assertTrue(receipt.get("usable_army_observed").booleanValue());
                assertTrue(receipt.get("next_formal").isNull());
            }
        }
        assertTrue(count >= 29);
    }
    @Test void sdkOriginalFloatTokensAndLargeIdsSurviveRelocation() {
        var source = new HolySdkJson.Source(raw("{\"planned\":{\"sdk\":1.0,\"zero\":-0.0,\"id\":18446744073709551615,\"empty\":[],\"nil\":null}}"));
        ObjectNode result = StrictJson.object(); result.set("result", source.tree().get("planned"));
        String output = new String(source.merge(result, "/absent", Map.of("/result", "/planned")), StandardCharsets.UTF_8);
        assertEquals("{\"result\":{\"sdk\":1.0,\"zero\":-0.0,\"id\":18446744073709551615,\"empty\":[],\"nil\":null}}", output);
        assertThrows(IllegalArgumentException.class, () -> new HolySdkJson.Source(raw("{\"x\":1,\"x\":2}")));
    }
    @Test void actualPortPreservesSdkTypesWhileItsDomainIgnoresUnownedObservers() {
        String observer = "{\"float\":1.0,\"zero\":-0.0,\"id\":18446744073709551615,\"empty\":[],\"nil\":null}";
        String input = "{\"operation\":\"plan\",\"stage\":\"prepare\",\"request\":{"
                + "\"schema\":\"xar.ck3.holy-reinforcement-plan-input.v1\",\"snapshot\":{},"
                + "\"planned\":{\"plan\":{},\"sdk\":" + observer + "},\"bridge_capabilities\":[],"
                + "\"query_available\":false,\"holy_context\":null,\"query_error\":null}}";
        byte[] output = assertInstanceOf(ProjectionResult.Succeeded.class, callRaw(false, raw(input))).result().bytes();
        assertTrue(new String(output, StandardCharsets.UTF_8).contains("\"sdk\":" + observer));
    }
    @Test void ownedRequestTokensRejectEqualWrongTypesAndInnerAliases() {
        for (String token : new String[]{"true", "1.0", "\"1\"", "null"}) {
            byte[] original = raw("{\"operation\":\"request\",\"request\":{\"schema\":\"xar.ck3.holy-hire-request-input.v1\",\"holy_order_id\":" + token + ",\"expected_revision\":1}}");
            assertInstanceOf(ProjectionResult.Rejected.class, callRaw(true, original));
        }
        assertInstanceOf(ProjectionResult.Rejected.class, call(true, "REQUEST", null, StrictJson.object()));
        assertInstanceOf(ProjectionResult.Rejected.class, call(false, "plan", "retry", StrictJson.object()));
    }
}
