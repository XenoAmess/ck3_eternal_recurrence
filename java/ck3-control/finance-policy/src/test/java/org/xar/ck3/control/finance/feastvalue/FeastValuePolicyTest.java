package org.xar.ck3.control.finance.feastvalue;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.finance.feastvalue.FeastStage5ValuePolicy.Amounts;
import org.xar.ck3.control.finance.feastvalue.FeastStage5ValuePolicy.Assessment;
import org.xar.ck3.control.finance.feastvalue.FeastStage5ValuePolicy.Decision;
import org.xar.ck3.control.finance.feastvalue.FeastStage5ValuePolicy.Reason;
import org.xar.ck3.control.finance.feastvalue.FeastStage5ValuePolicy.Request;
import org.xar.ck3.control.finance.feastvalue.FeastStage5ValuePolicy.Status;

final class FeastValuePolicyTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String GOLDEN_SHA = "ec0f87133decf60ea87898527e2deaa6e1f18c7c9a4b92da538fb16731bd59e9";
    private static final String PRODUCER_SHA = "833d2503ef944d8a46516a94fbf3342379c50a32bfef769e9e27463094b2ba0e";

    @TestFactory
    Stream<DynamicTest> comparesActualProducerGoldenAndRequestRoundTrip() throws IOException {
        JsonNode golden = golden();
        assertEquals(38, golden.get("cases").size());
        return java.util.stream.StreamSupport.stream(golden.get("cases").spliterator(), false)
                .map(row -> DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
            Request request = FeastValueCodec.decodeRequest(JSON.writeValueAsBytes(row.get("input")));
            Assessment assessment = FeastStage5ValuePolicy.assess(request);
            assertEquals(row.get("expected"), JSON.readTree(FeastValueCodec.encodeAssessment(assessment)));
            assertEquals(request, FeastValueCodec.decodeRequest(FeastValueCodec.encodeRequest(request)));
        }));
    }

    @Test
    void fixtureBindsActualUnchangedProducerAndHasNoRuntimePythonDependency() throws IOException, NoSuchAlgorithmException {
        byte[] bytes = goldenBytes();
        assertEquals(GOLDEN_SHA, HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        JsonNode golden = JSON.readTree(bytes);
        assertEquals(PRODUCER_SHA, golden.get("source_sha256").textValue());
        assertEquals("xenoamess-full-tower-eb9d2c1186", golden.get("machine_id").textValue());
        assertTrue(golden.get("capture_scope").textValue().startsWith("actual unchanged Python leaf invoked"));
    }

    @Test
    void rejectsMissingAndUnknownFieldsRatherThanTreatingMissingAsNull() throws IOException {
        ObjectNode base = baseline();
        List<String> fields = java.util.stream.StreamSupport.stream(
                java.util.Spliterators.spliteratorUnknownSize(base.fieldNames(), 0), false).toList();
        for (String field : fields) {
            ObjectNode changed = base.deepCopy(); changed.remove(field);
            assertThrows(IllegalArgumentException.class, () -> FeastValueCodec.decodeRequest(JSON.writeValueAsBytes(changed)), field);
        }
        ObjectNode extra = base.deepCopy(); extra.put("reserved_gold", 0);
        assertThrows(IllegalArgumentException.class, () -> FeastValueCodec.decodeRequest(JSON.writeValueAsBytes(extra)));
        ObjectNode explicitUnknown = base.deepCopy(); explicitUnknown.putNull("war_cash_reserve_raw");
        Assessment actual = FeastStage5ValuePolicy.assess(FeastValueCodec.decodeRequest(JSON.writeValueAsBytes(explicitUnknown)));
        assertEquals(Status.MISSING_INPUT, actual.status());
        assertEquals(Reason.WAR_CASH_RESERVE_UNOBSERVED, actual.reason());
    }

    @Test
    void rejectsBooleanFloatingStringNegativeAndNullIntegerSubstitutes() throws IOException {
        for (String field : List.of("planning_stage", "expected_nonhost_guest_count", "gold_floor_raw", "active_war_count", "war_cash_reserve_raw")) {
            for (JsonNode invalid : List.of(JSON.getNodeFactory().booleanNode(true), JSON.getNodeFactory().numberNode(1.0),
                    JSON.getNodeFactory().textNode("1"))) {
                ObjectNode changed = baseline(); changed.set(field, invalid);
                assertThrows(IllegalArgumentException.class, () -> FeastValueCodec.decodeRequest(JSON.writeValueAsBytes(changed)), field);
            }
        }
        for (String field : List.of("expected_nonhost_guest_count", "gold_floor_raw", "active_war_count", "war_cash_reserve_raw")) {
            ObjectNode changed = baseline(); changed.put(field, -1);
            assertThrows(IllegalArgumentException.class, () -> FeastValueCodec.decodeRequest(JSON.writeValueAsBytes(changed)), field);
        }
        ObjectNode noStage = baseline(); noStage.putNull("planning_stage");
        assertThrows(IllegalArgumentException.class, () -> FeastValueCodec.decodeRequest(JSON.writeValueAsBytes(noStage)));
    }

    @Test
    void rejectsMalformedResourceVectorsAndBooleanAvailabilityCoercion() throws IOException {
        for (String field : List.of("configured_cost_raw", "balance_raw", "reserved_raw", "balance_available")) {
            ObjectNode missingSlot = baseline(); missingSlot.putArray(field).add(0).add(0).add(0);
            assertThrows(IllegalArgumentException.class, () -> FeastValueCodec.decodeRequest(JSON.writeValueAsBytes(missingSlot)), field);
            ObjectNode notVector = baseline(); notVector.put(field, "0,0,0,0");
            assertThrows(IllegalArgumentException.class, () -> FeastValueCodec.decodeRequest(JSON.writeValueAsBytes(notVector)), field);
        }
        for (String field : List.of("configured_cost_raw", "balance_raw", "reserved_raw")) {
            for (JsonNode invalid : List.of(JSON.getNodeFactory().booleanNode(true), JSON.getNodeFactory().numberNode(1.0),
                    JSON.getNodeFactory().textNode("1"), JSON.getNodeFactory().numberNode(-1))) {
                ObjectNode changed = baseline(); ArrayNode vector = resourceVector(changed, field); vector.set(0, invalid);
                assertThrows(IllegalArgumentException.class, () -> FeastValueCodec.decodeRequest(JSON.writeValueAsBytes(changed)), field);
            }
        }
        for (String field : List.of("balance_raw", "reserved_raw")) {
            ObjectNode changed = baseline(); resourceVector(changed, field).set(0, JSON.getNodeFactory().nullNode());
            assertThrows(IllegalArgumentException.class, () -> FeastValueCodec.decodeRequest(JSON.writeValueAsBytes(changed)), field);
        }
        ObjectNode numericAvailability = baseline(); resourceVector(numericAvailability, "balance_available").set(0, JSON.getNodeFactory().numberNode(1));
        assertThrows(IllegalArgumentException.class, () -> FeastValueCodec.decodeRequest(JSON.writeValueAsBytes(numericAvailability)));
    }

    @Test
    void rejectsDuplicateKeysTrailingJsonMalformedUtf8AndOverBudget() throws IOException {
        String base = JSON.writeValueAsString(baseline());
        String duplicate = "{\"activity_key\":\"duplicate\"," + base.substring(1);
        assertThrows(IllegalArgumentException.class, () -> FeastValueCodec.decodeRequest(duplicate.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> FeastValueCodec.decodeRequest((base + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> FeastValueCodec.decodeRequest(new byte[] {(byte) 0xC3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> FeastValueCodec.decodeRequest(new byte[FeastValueCodec.MAX_BYTES + 1]));
        assertThrows(IllegalArgumentException.class, () -> FeastValueCodec.decodeRequest(new byte[0]));
        assertThrows(IllegalArgumentException.class, () -> FeastValueCodec.decodeRequest("[]".getBytes(StandardCharsets.UTF_8)));
    }

    @Test
    void requiresRealBooleanForNativeAndPeacefulGates() throws IOException {
        for (String field : List.of("final_can_start", "peaceful_spend_allowed")) {
            for (JsonNode invalid : List.of(JSON.getNodeFactory().numberNode(1), JSON.getNodeFactory().textNode("true"))) {
                ObjectNode changed = baseline(); changed.set(field, invalid);
                assertThrows(IllegalArgumentException.class, () -> FeastValueCodec.decodeRequest(JSON.writeValueAsBytes(changed)), field);
            }
        }
    }

    @Test
    void constructorsEnforceNonnegativeAmountsAndAssessmentBranch() throws IOException {
        assertThrows(IllegalArgumentException.class, () -> new Amounts(BigInteger.valueOf(-1), BigInteger.ZERO, BigInteger.ZERO, BigInteger.ZERO));
        Request request = FeastValueCodec.decodeRequest(JSON.writeValueAsBytes(baseline()));
        assertThrows(IllegalArgumentException.class, () -> new Assessment(Decision.START, Status.READY,
                Reason.NATIVE_FINAL_START_UNAVAILABLE, true, request.configuredCostRaw(),
                Optional.of(request.configuredCostRaw().observed()), Optional.of(request.reservedRaw())));
        Assessment actual = FeastStage5ValuePolicy.assess(request);
        assertTrue(actual.resourceCommitmentRaw().isPresent());
        assertFalse(actual.submitReserveRaw().orElseThrow().equals(request.reservedRaw()));
    }

    private static ObjectNode baseline() throws IOException {
        JsonNode request = golden().get("cases").get(0).get("input");
        if (!(request instanceof ObjectNode object)) throw new IOException("golden baseline is not object");
        return object.deepCopy();
    }
    private static ArrayNode resourceVector(ObjectNode root, String name) throws IOException {
        if (!(root.get(name) instanceof ArrayNode vector)) throw new IOException("fixture resource is not array");
        return vector;
    }
    private static JsonNode golden() throws IOException { return JSON.readTree(goldenBytes()); }
    private static byte[] goldenBytes() throws IOException {
        try (InputStream input = FeastValuePolicyTest.class.getResourceAsStream("/feastvalue/producer-golden-v1.json")) {
            if (input == null) throw new IOException("required producer fixture unavailable");
            return input.readAllBytes();
        }
    }
}
