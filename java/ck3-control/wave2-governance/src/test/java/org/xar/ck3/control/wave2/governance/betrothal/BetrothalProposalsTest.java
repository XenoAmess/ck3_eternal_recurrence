package org.xar.ck3.control.wave2.governance.betrothal;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

class BetrothalProposalsTest {
    private static JsonNode golden() throws IOException {
        try (InputStream input = BetrothalProposalsTest.class.getResourceAsStream("/betrothal/python-golden-v1.json")) {
            assertNotNull(input, "actual committed Python producer golden is mandatory");
            JsonNode result = BetrothalCodec.readJson(input.readAllBytes());
            assertEquals("xar.ck3.betrothal-python-golden.v1", result.path("schema").textValue());
            assertFalse(result.path("machine_id").textValue().isEmpty());
            assertFalse(result.path("observed_at_utc").textValue().isEmpty());
            assertEquals(10, result.path("original_tests_run").intValue());
            assertEquals(0, result.path("original_failures").intValue());
            assertEquals(0, result.path("original_errors").intValue());
            assertEquals(0, result.path("original_skipped").intValue());
            assertEquals(12, result.path("build_cases").size());
            assertEquals(22, result.path("adapt_cases").size());
            assertEquals(6, result.path("source_refs").size());
            assertEquals(35, result.path("native_fixture_refs").size());
            return result;
        }
    }

    private static byte[] raw(JsonNode value) { return value.toString().getBytes(StandardCharsets.UTF_8); }
    private static ObjectNode baseBuild(JsonNode golden) { return (ObjectNode) golden.get("base_build_request").deepCopy(); }
    private static ObjectNode baseAdapt(JsonNode golden) { return (ObjectNode) golden.get("base_adapt_request").deepCopy(); }

    private static ObjectNode patched(ObjectNode base, JsonNode patches) {
        ObjectNode result = base.deepCopy();
        for (JsonNode patch : patches) {
            JsonNode path = patch.get("path"), parent = result;
            for (int index = 0; index < path.size() - 1; index++) {
                JsonNode key = path.get(index); parent = key.isIntegralNumber() ? parent.get(key.intValue()) : parent.get(key.textValue());
            }
            JsonNode key = path.get(path.size() - 1);
            if (parent instanceof ObjectNode object) {
                if (patch.path("remove").asBoolean(false)) { object.remove(key.textValue()); }
                else { object.set(key.textValue(), patch.get("value").deepCopy()); }
            } else if (parent instanceof ArrayNode array) {
                if (patch.path("remove").asBoolean(false)) { array.remove(key.intValue()); }
                else { array.set(key.intValue(), patch.get("value").deepCopy()); }
            } else { fail("invalid committed golden patch"); }
        }
        return result;
    }

    @Test
    void actualProducerBuildCorpusMatchesEveryRetainedField() throws IOException {
        JsonNode golden = golden();
        for (JsonNode testCase : golden.get("build_cases")) {
            BuildInput input = BetrothalCodec.decodeBuild(raw(patched(baseBuild(golden), testCase.get("patches"))));
            ResourceProposal resource = BetrothalProposals.build(input);
            assertEquals(testCase.get("expected_resource"), BetrothalCodec.resourceNode(resource), testCase.get("name").textValue());
        }
    }

    @Test
    void actualProducerM5AdapterAcceptsAndRejectsTheSameBindings() throws IOException {
        JsonNode golden = golden();
        for (JsonNode testCase : golden.get("adapt_cases")) {
            AdaptInput input = BetrothalCodec.decodeAdapt(raw(patched(baseAdapt(golden), testCase.get("patches"))));
            JsonNode expected = testCase.get("expected"); String name = testCase.get("name").textValue();
            if (expected.get("accepted").booleanValue()) {
                assertEquals(expected.get("proposal"), BetrothalCodec.opportunityNode(BetrothalProposals.adapt(input)), name);
            } else {
                IllegalArgumentException error = assertThrows(IllegalArgumentException.class, () -> BetrothalProposals.adapt(input), name);
                assertEquals(expected.get("error_message").textValue(), error.getMessage(), name);
            }
        }
    }

    @Test
    void resourceRoundTripPreservesSignedCostsMissingNullAndOpaqueEvidence() throws IOException {
        JsonNode golden = golden();
        for (JsonNode testCase : golden.get("build_cases")) {
            ResourceProposal resource = BetrothalProposals.build(BetrothalCodec.decodeBuild(raw(patched(baseBuild(golden), testCase.get("patches")))));
            byte[] first = BetrothalCodec.encodeResource(resource);
            ResourceProposal restored = BetrothalCodec.decodeResource(first);
            assertEquals(resource, restored, testCase.get("name").textValue());
            assertArrayEquals(first, BetrothalCodec.encodeResource(restored));
        }
        ObjectNode missing = baseBuild(golden());
        ObjectNode costs = (ObjectNode) missing.get("relation").get("betrothal_actionability").get("generic_costs");
        costs.remove("merit_raw");
        assertEquals(Presence.MISSING, BetrothalCodec.decodeBuild(raw(missing)).relation().actionability().costs().amounts().get(CostTerm.MERIT).presence());
        costs.putNull("merit_raw");
        assertEquals(Presence.NULL, BetrothalCodec.decodeBuild(raw(missing)).relation().actionability().costs().amounts().get(CostTerm.MERIT).presence());
        String decimalEvidence = baseBuild(golden).toString().replace("\"gold_raw\":0", "\"source_extension\":1.0,\"gold_raw\":0");
        ResourceProposal decimalResource = BetrothalProposals.build(BetrothalCodec.decodeBuild(decimalEvidence.getBytes(StandardCharsets.UTF_8)));
        assertInstanceOf(DecimalValue.class, decimalResource.immediateGenericCosts().extensions().values().get("source_extension"));
        byte[] decimalWire = BetrothalCodec.encodeResource(decimalResource);
        assertTrue(BetrothalCodec.readJson(decimalWire).get("immediate_generic_costs").get("source_extension").isFloatingPointNumber());
        assertEquals(decimalResource, BetrothalCodec.decodeResource(decimalWire));
    }

    @Test
    void builderRetainsFormalHoldAndNeverMakesASecondCommitment() throws IOException {
        ObjectNode input = baseBuild(golden()); input.put("selected", false); input.putArray("reasons").add("unresolved_original_action");
        ResourceProposal resource = BetrothalProposals.build(BetrothalCodec.decodeBuild(raw(input)));
        assertEquals(Boolean.FALSE, resource.selected()); assertEquals(Boolean.FALSE, resource.formalActionReady());
        assertEquals(Boolean.FALSE, resource.resourceReservationPerformed()); assertEquals(Boolean.FALSE, resource.existingCommitment().newBetrothalCommitment());
        assertEquals("unknown", resource.futureAllianceObligation()); assertEquals(NullValue.INSTANCE, resource.allianceEstablished());
        assertEquals(List.of("unresolved_original_action"), resource.reasons());
        Frame frame = resource.sourceFrame();
        assertThrows(IllegalArgumentException.class, () -> BetrothalProposals.adapt(new AdaptInput(frame, new Plan(BetrothalProposals.SUBMIT_STEP, resource))));
    }

    @Test
    void eachEnvelopeFieldIsRequiredAndUnknownFieldsReject() throws IOException {
        for (boolean build : List.of(true, false)) {
            ObjectNode base = build ? baseBuild(golden()) : baseAdapt(golden());
            List<String> keys = new ArrayList<>(); base.fieldNames().forEachRemaining(keys::add);
            for (String key : keys) {
                ObjectNode missing = base.deepCopy(); missing.remove(key);
                assertThrows(IllegalArgumentException.class, () -> { if (build) { BetrothalCodec.decodeBuild(raw(missing)); } else { BetrothalCodec.decodeAdapt(raw(missing)); } }, key);
            }
            ObjectNode unknown = base.deepCopy(); unknown.put("fallback", true);
            assertThrows(IllegalArgumentException.class, () -> { if (build) { BetrothalCodec.decodeBuild(raw(unknown)); } else { BetrothalCodec.decodeAdapt(raw(unknown)); } });
        }
    }

    @Test
    void integerFieldsRejectOriginalFloatBooleanAndStringTokensWithoutReserializingThem() throws IOException {
        String base = baseBuild(golden()).toString();
        for (String token : List.of("true", "false", "29829.0", "\"29829\"", "0", "-1", "2147483648")) {
            String changed = base.replace("\"character_id\":29829", "\"character_id\":" + token);
            assertNotEquals(base, changed);
            assertThrows(IllegalArgumentException.class, () -> BetrothalCodec.decodeBuild(changed.getBytes(StandardCharsets.UTF_8)), token);
        }
        for (String token : List.of("0.0", "false", "\"0\"")) {
            String changed = base.replace("\"gold_raw\":0", "\"gold_raw\":" + token);
            assertThrows(IllegalArgumentException.class, () -> BetrothalCodec.decodeBuild(changed.getBytes(StandardCharsets.UTF_8)), token);
        }
        String fractionalScale = base.replace("\"raw_scale\":100000", "\"raw_scale\":100000.0");
        assertThrows(IllegalArgumentException.class, () -> BetrothalCodec.decodeBuild(fractionalScale.getBytes(StandardCharsets.UTF_8)));
    }

    @Test
    void signed64CostAndUnsignedExactFrameBoundariesAreExplicit() throws IOException {
        ObjectNode input = baseBuild(golden());
        ObjectNode costs = (ObjectNode) input.get("relation").get("betrothal_actionability").get("generic_costs");
        costs.put("gold_raw", BigInteger.ONE.shiftLeft(63));
        assertThrows(IllegalArgumentException.class, () -> BetrothalCodec.decodeBuild(raw(input)));
        costs.put("gold_raw", BigInteger.ONE.shiftLeft(63).negate().subtract(BigInteger.ONE));
        assertThrows(IllegalArgumentException.class, () -> BetrothalCodec.decodeBuild(raw(input)));
        costs.put("gold_raw", BigInteger.ZERO);
        ((ObjectNode) input.get("snapshot")).put("native_revision", new BigInteger("18446744073709551615"));
        assertEquals(new BigInteger("18446744073709551615"), BetrothalCodec.decodeBuild(raw(input)).frame().nativeRevision());
        ((ObjectNode) input.get("snapshot")).put("date_raw", -1);
        assertThrows(IllegalArgumentException.class, () -> BetrothalCodec.decodeBuild(raw(input)));
    }

    @Test
    void duplicateKeyTrailingTokenMalformedUtf8AndOversizeReject() throws IOException {
        String base = baseBuild(golden()).toString();
        assertThrows(IllegalArgumentException.class, () -> BetrothalCodec.decodeBuild(("{\"selected\":false," + base.substring(1)).getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> BetrothalCodec.decodeBuild((base + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> BetrothalCodec.decodeBuild(new byte[] {(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> BetrothalCodec.decodeBuild(new byte[BetrothalCodec.MAX_BYTES + 1]));
    }

    @Test
    void inputTreeMutationCannotChangeTheConstructedResource() throws IOException {
        ObjectNode input = baseBuild(golden());
        ObjectNode relation = (ObjectNode) input.get("relation");
        relation.putObject("current_first_heir_descendants_v1").putArray("children").add(1);
        BuildInput decoded = BetrothalCodec.decodeBuild(raw(input));
        ResourceProposal before = BetrothalProposals.build(decoded);
        ((ArrayNode) relation.get("current_first_heir_descendants_v1").get("children")).add(2);
        assertEquals(before, BetrothalProposals.build(decoded));
        ObjectValue expected = new ObjectValue(java.util.Map.of("children", new ArrayValue(List.of(new IntegerValue(BigInteger.ONE)))));
        assertEquals(expected, before.descendants());
    }
}
