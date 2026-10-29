package org.xar.ck3.control.wave2.military.projection;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.*;
import org.xar.ck3.control.wave2.military.coalitionreceipt.CoalitionExecutionReceipt;

/** Actual registered branch regression. Mandatory original resources; no external process, skip or synthetic qualification. */
final class CoalitionReceiptProjectionBranchTest {
    @Test void originalTopReceiptCasesEnterActualRegisteredBranch() throws IOException {
        JsonNode golden = fixture(); int accepted = 0, rejected = 0;
        for (JsonNode sample : golden.path("cases")) {
            // Summary failures include the stronger lease/domain normalization, covered by the unchanged original test.
            if (sample.path("summary").booleanValue() && !sample.path("expected").path("accepted").booleanValue()) continue;
            ObjectNode input = golden.path("base").deepCopy();
            for (JsonNode edit : sample.path("edits")) apply(input, edit);
            ObjectNode payload = StrictJson.object().put("operation", "receipt-validate");
            payload.set("frame", input.get("frame")); payload.set("expected_request_id", input.get("expected_request_id"));
            ProjectionResult result = call(raw(payload));
            if (sample.path("expected").path("accepted").booleanValue()) {
                JsonNode output = success(result);
                assertEquals(sample.path("expected").get("receipt"), output.get("receipt"), sample.path("id").textValue());
                assertEquals(input.path("frame").get("result"), output.get("result"));
                accepted++;
            } else {
                assertInstanceOf(ProjectionResult.Rejected.class, result, sample.path("id").textValue()); rejected++;
            }
        }
        assertTrue(accepted >= 5); assertTrue(rejected >= 40);
    }

    @Test void rawOpaqueNumbersAndStringsArePreservedButCannotQualify() {
        String result = "{\"step\":\"" + CoalitionExecutionReceipt.STEP + "\",\"accepted\":true,\"status\":\"available\","
                + "\"private_build\":false,\"read_only\":true,\"advertised\":true,\"domain_key\":\""
                + CoalitionExecutionReceipt.DOMAIN_KEY + "\",\"" + CoalitionExecutionReceipt.DOMAIN_KEY
                + "\":{\"integer\":1,\"float\":1.0,\"negative_zero\":-0.0,\"exponent\":1e0,\"text\":\"a\\\"b雪\"}}";
        String frame = "{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\"raw\","
                + "\"ok\":true,\"execution_receipt\":{\"ticket\":13,\"query_sequence\":13,\"capture_epoch\":17},\"result\":" + result + "}";
        byte[] output = assertInstanceOf(ProjectionResult.Succeeded.class, call(utf8(
                "{\"operation\":\"receipt-validate\",\"expected_request_id\":\"raw\",\"frame\":" + frame + "}"))).result().bytes();
        assertArrayEquals(utf8(result), new HolySdkJson.Source(output).token("/result"));
        JsonNode originalFrame = StrictJson.parse(utf8(frame));
        var command = CoalitionExecutionReceipt.validate(originalFrame, "raw");
        assertThrows(IllegalArgumentException.class, () -> CoalitionExecutionReceipt.normalizeAgainstLease(command, StrictJson.object(), StrictJson.object(), null));
        assertInstanceOf(ProjectionResult.Rejected.class, call(utf8("{\"operation\":\"history-projection\",\"result\":" + result + "}")));
        for (String token : List.of("true", "13.0", "1.3e1", "\"13\"")) {
            assertInstanceOf(ProjectionResult.Rejected.class, call(utf8(
                    "{\"operation\":\"receipt-validate\",\"expected_request_id\":\"raw\",\"frame\":"
                    + frame.replace("\"ticket\":13", "\"ticket\":" + token) + "}")));
        }
    }

    @Test void realEnrichedHistoryAgreesWithOriginalSummaryAndNeverBecomesCurrentBody() throws IOException {
        JsonNode golden = fixture(); ObjectNode input = golden.path("base").deepCopy();
        var command = CoalitionExecutionReceipt.validate(input.get("frame"), input.path("expected_request_id").textValue());
        var current = CoalitionExecutionReceipt.normalizeAgainstLease(command, input.get("snapshot"), input.get("declaration"), null);
        ObjectNode enriched = command.resultJson();
        enriched.set("execution_receipt", command.receipt().toJson()); enriched.put("native_request_id", command.requestId());
        enriched.put("unrelated_actual_driver_metadata", "projected away");
        ObjectNode payload = StrictJson.object().put("operation", "history-projection"); payload.set("result", enriched);
        JsonNode summary = success(call(raw(payload)));
        assertEquals(golden.path("cases").get(0).path("expected").get("summary"), summary);
        assertEquals(CoalitionExecutionReceipt.historySummary(current), summary);
        assertFalse(summary.path("full_result_preserved").booleanValue());
        assertFalse(summary.has(CoalitionExecutionReceipt.DOMAIN_KEY));
        assertThrows(IllegalArgumentException.class, () -> CoalitionExecutionReceipt.validate(summary, command.requestId()));
        // A false accepted field is retained in history; its typed container conveys no validation authority.
        enriched.put("accepted", false);
        assertFalse(success(call(raw(payload))).path("accepted").booleanValue());
        for (String token : List.of("true", "1500.0", "\"1500\"")) {
            byte[] malformed = utf8(new String(raw(payload), StandardCharsets.UTF_8)
                    .replace("\"actor_lower_soldiers\":1500", "\"actor_lower_soldiers\":" + token));
            assertEquals(ProjectionError.Code.DOMAIN_REJECTED, rejected(call(malformed)).error().code());
        }
    }

    @Test void legacyNormalizeHasNoAliasOrShapeFallbackAndStillUsesActualIndependentBinding() throws IOException {
        ObjectNode input = fixture().path("base").deepCopy();
        ObjectNode payload = StrictJson.object();
        payload.set("value", input.path("frame").path("result").get(CoalitionExecutionReceipt.DOMAIN_KEY));
        payload.set("snapshot", input.get("snapshot")); payload.set("expected_declaration", input.get("declaration"));
        ObjectNode binding = input.path("frame").path("execution_receipt").deepCopy();
        binding.set("request_id", input.get("expected_request_id"));
        payload.set("expected_request_binding", binding); payload.set("expected_request_id", input.get("expected_request_id"));
        payload.putNull("expected_capture_epoch");
        assertEquals(1500, success(call(raw(payload))).path("actor_lower_soldiers").intValue());
        binding.put("ticket", 14);
        assertEquals(ProjectionError.Code.DOMAIN_REJECTED, rejected(call(raw(payload))).error().code());
        payload.put("operation", "normalize");
        assertEquals(ProjectionError.Code.INVALID_PAYLOAD, rejected(call(raw(payload))).error().code());
        for (String body : List.of("{}", "{\"operation\":\"receipt-validate\"}", "{\"operation\":null}",
                "{\"operation\":\"history-projection\",\"result\":{},\"extra\":1}",
                "{\"operation\":\"history-projection\",\"operation\":\"receipt-validate\"}")) {
            assertInstanceOf(ProjectionResult.Rejected.class, call(utf8(body)));
        }
        byte[] oversized = new byte[65_537]; java.util.Arrays.fill(oversized, (byte) ' ');
        assertThrows(IllegalArgumentException.class, () -> CoalitionReceiptProjectionBranch.decode(oversized));
    }

    @Test void host04DistinguishesExpectedValidatorRejectionFromAlgorithmAndEncoderBugs() {
        IllegalArgumentException bug = new IllegalArgumentException("algorithm bug");
        for (String stage : List.of("guard", "algorithm", "algorithm-contract", "encoder")) {
            RegisteredProjection registered = RegisteredProjection.of(new ProjectionPort<String, String>() {
                @Override public ProjectionOperation operation() { return ProjectionOperation.MILITARY_COALITION_NORMALIZE; }
                @Override public String decode(byte[] raw) { StrictJson.parse(raw); return stage; }
                @Override public String project(String value) {
                    if (value.equals("guard")) { CoalitionExecutionReceipt.historyProjection(StrictJson.object()); return value; }
                    if (value.equals("algorithm")) throw bug;
                    if (value.equals("algorithm-contract")) throw new ContractViolationException("result invariant bug");
                    return value;
                }
                @Override public byte[] encode(String value) { throw new IllegalArgumentException("serializer bug"); }
            });
            ProjectionError.Code expected = stage.equals("guard") ? ProjectionError.Code.DOMAIN_REJECTED
                    : (stage.equals("algorithm") || stage.equals("algorithm-contract")) ? ProjectionError.Code.PROJECTION_FAILED : ProjectionError.Code.INVALID_RESULT;
            assertEquals(expected, rejected(registered.execute(envelope(utf8("{}")))).error().code());
        }
    }

    private static ProjectionResult call(byte[] payload) {
        RegisteredProjection actual = new MilitaryProjectionPortCatalog().registrations().stream()
                .filter(row -> row.operation() == ProjectionOperation.MILITARY_COALITION_NORMALIZE).findFirst().orElseThrow();
        return actual.execute(envelope(payload));
    }
    private static ProjectionCall envelope(byte[] payload) {
        return new ProjectionCall(new ProjectionCall.Identity("receipt-actual-branch", ProjectionOperation.MILITARY_COALITION_NORMALIZE),
                ProjectionJson.object(payload, ProjectionJson.MAX_BYTES));
    }
    private static ProjectionResult.Rejected rejected(ProjectionResult result) { return assertInstanceOf(ProjectionResult.Rejected.class, result); }
    private static JsonNode success(ProjectionResult result) {
        return StrictJson.parse(assertInstanceOf(ProjectionResult.Succeeded.class, result).result().bytes());
    }
    private static JsonNode fixture() throws IOException {
        try (InputStream input = CoalitionReceiptProjectionBranchTest.class.getResourceAsStream("/coalitionreceipt/original-producer-golden01.json")) {
            assertNotNull(input, "mandatory unchanged actual original receipt golden");
            byte[] raw = input.readNBytes(51_201); assertTrue(raw.length <= 51_200);
            return StrictJson.parse(raw, 51_200);
        }
    }
    private static byte[] utf8(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    /** Test-only encoding preserves the JSON number kind of edited fixture nodes. Lexical retention is tested separately. */
    private static byte[] raw(JsonNode value) {
        if (value.isFloatingPointNumber()) {
            String text = value.decimalValue().toPlainString();
            return utf8(text.indexOf('.') < 0 ? text + ".0" : text);
        }
        if (value.isObject() || value.isArray()) {
            StringBuilder out = new StringBuilder(value.isObject() ? "{" : "["); boolean first = true;
            if (value.isObject()) {
                var fields = value.properties().iterator();
                while (fields.hasNext()) {
                    var field = fields.next(); if (!first) out.append(','); first = false;
                    out.append(new String(StrictJson.canonical(com.fasterxml.jackson.databind.node.TextNode.valueOf(field.getKey())), StandardCharsets.UTF_8)).append(':');
                    out.append(new String(raw(field.getValue()), StandardCharsets.UTF_8));
                }
            } else for (JsonNode item : value) {
                if (!first) out.append(','); first = false; out.append(new String(raw(item), StandardCharsets.UTF_8));
            }
            return utf8(out.append(value.isObject() ? '}' : ']').toString());
        }
        return StrictJson.canonical(value);
    }
    private static void apply(ObjectNode input, JsonNode edit) {
        JsonNode path = edit.get("path"), parent = input;
        for (int i = 0; i < path.size() - 1; i++) parent = path.get(i).isTextual() ? parent.get(path.get(i).textValue()) : parent.get(path.get(i).intValue());
        JsonNode key = path.get(path.size() - 1);
        if (edit.path("remove").booleanValue()) {
            if (parent instanceof ObjectNode object) object.remove(key.textValue()); else ((ArrayNode) parent).remove(key.intValue());
        } else {
            JsonNode value = StrictJson.parse(utf8(edit.get("value_json").textValue()));
            if (parent instanceof ObjectNode object) object.set(key.textValue(), value); else ((ArrayNode) parent).set(key.intValue(), value);
        }
    }
}
