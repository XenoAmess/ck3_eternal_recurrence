package org.xar.ck3.control.wave2.military.armyinventory;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.cfg.JsonNodeFeature;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.military.armyinventory.ArmyInventoryValidation.Check;
import org.xar.ck3.control.wave2.military.armyinventory.ArmyInventoryValidation.Reason;

final class ArmyInventoryValidationTest {
    private static final ObjectMapper WIRE = new ObjectMapper()
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .configure(JsonNodeFeature.STRIP_TRAILING_BIGDECIMAL_ZEROES, false);

    private static JsonNode golden() throws IOException {
        try (InputStream stream = ArmyInventoryValidationTest.class.getResourceAsStream("/armyinventory/producer-golden-v1.json")) {
            if (stream == null) { throw new IOException("actual producer golden must be committed before default tests run"); }
            return WIRE.readTree(stream);
        }
    }
    private static ObjectNode base(String name) throws IOException { return (ObjectNode) golden().get("bases").get(name).deepCopy(); }
    private static byte[] bytes(JsonNode value) throws IOException { return WIRE.writeValueAsBytes(value); }

    @TestFactory Stream<DynamicTest> actualProducerCases() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.army-inventory-producer-golden/v1", golden.get("schema").textValue());
        assertTrue(golden.get("cases").size() >= 70);
        return java.util.stream.StreamSupport.stream(golden.get("cases").spliterator(), false).map(item ->
                DynamicTest.dynamicTest(item.get("name").textValue(), () -> {
                    ObjectNode input = (ObjectNode) golden.get("bases").get(item.get("base").textValue()).deepCopy();
                    for (JsonNode patch : item.get("patches")) { apply(input, patch); }
                    JsonNode actual = StrictJson.parse(ArmyInventoryValidation.validate(bytes(input)));
                    assertEquals(item.get("expected"), actual);
                    assertFalse(actual.get("date_or_action_authorized").booleanValue());
                }));
    }

    private static void apply(ObjectNode root, JsonNode patch) {
        JsonNode path = patch.get("path"); JsonNode target = root;
        for (int index = 0; index < path.size() - 1; index++) {
            JsonNode segment = path.get(index);
            target = segment.isIntegralNumber() ? target.get(segment.intValue()) : target.get(segment.textValue());
        }
        JsonNode key = path.get(path.size() - 1);
        if (target instanceof ObjectNode object) {
            if (patch.get("op").textValue().equals("remove")) { object.remove(key.textValue()); }
            else { object.set(key.textValue(), patch.get("value").deepCopy()); }
        } else if (target instanceof ArrayNode array && key.isIntegralNumber()) {
            if (patch.get("op").textValue().equals("remove")) { array.remove(key.intValue()); }
            else { array.set(key.intValue(), patch.get("value").deepCopy()); }
        } else { throw new IllegalArgumentException("invalid frozen golden patch"); }
    }

    @Test void rawFloatingExpectedAndSubjectTokensReachTheIntegerGuard() throws IOException {
        for (String token : List.of("true", "53219928.0", "\"53219928\"", "null")) {
            ObjectNode input = base("shape");
            ((ObjectNode) input.get("expected")).set("date_raw", WIRE.readTree(token));
            byte[] wire = bytes(input);
            assertTrue(new String(wire, StandardCharsets.UTF_8).contains("\"date_raw\":" + token));
            assertThrows(ContractViolationException.class, () -> ArmyInventoryValidation.validate(wire));
        }
        ObjectNode mailbox = base("mailbox"); mailbox.set("subject_army_id", WIRE.readTree("83886367.0"));
        byte[] raw = bytes(mailbox); assertTrue(new String(raw, StandardCharsets.UTF_8).contains("83886367.0"));
        assertThrows(ContractViolationException.class, () -> ArmyInventoryValidation.validate(raw));
    }

    @Test void wrongReceiptNumericTypesReturnReadOnlyRejection() throws IOException {
        for (String token : List.of("true", "7.0", "\"7\"", "null")) {
            ObjectNode input = base("shape");
            ((ObjectNode) input.get("receipt")).set("native_revision", WIRE.readTree(token));
            JsonNode result = StrictJson.parse(ArmyInventoryValidation.validate(bytes(input)));
            assertEquals("native_revision_mismatch", result.get("reason").textValue());
            assertFalse(result.get("valid").booleanValue());
        }
    }

    @Test void exactLargeIdentitySurvivesSerializationWithoutJavascriptNumber() {
        BigInteger id = BigInteger.ONE.shiftLeft(100);
        Check check = new Check(true, Reason.SHAPE_VALID_ONLY, List.of(id), List.of(id));
        JsonNode decoded = StrictJson.parse(ArmyInventoryValidation.encode(check));
        assertEquals(id, decoded.get("hostile_army_ids").get(0).bigIntegerValue());
        assertEquals(id, decoded.get("contact_hostile_army_ids").get(0).bigIntegerValue());
        assertFalse(check.dateOrActionAuthorized());
        assertThrows(UnsupportedOperationException.class, () -> check.hostileArmyIds().add(BigInteger.ONE));
    }

    @Test void malformedNewWrapperUnknownFieldsAndDuplicateKeysReject() throws IOException {
        ObjectNode input = base("shape"); input.put("alias", true);
        byte[] unknown = bytes(input);
        assertThrows(ContractViolationException.class, () -> ArmyInventoryValidation.validate(unknown));
        assertThrows(ContractViolationException.class, () -> ArmyInventoryValidation.validate(
                "{\"mode\":\"shape\",\"mode\":\"mailbox\"}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(ContractViolationException.class, () -> ArmyInventoryValidation.validate(new byte[]{(byte) 0xc3, 0x28}));
    }

    @Test void missingReceiptAndRequiredNullableFrameRemainDistinct() throws IOException {
        ObjectNode input = base("shape"); input.putNull("receipt");
        assertEquals("inventory_unavailable_or_partial", StrictJson.parse(ArmyInventoryValidation.validate(bytes(input))).get("reason").textValue());
        ObjectNode mailbox = base("mailbox"); ((ObjectNode) mailbox.get("current")).remove("active_event");
        assertEquals("public_frame_changed", StrictJson.parse(ArmyInventoryValidation.validate(bytes(mailbox))).get("reason").textValue());
    }

    @Test void mailboxRejectsBooleanIdentityDespiteNumericEquality() throws IOException {
        ObjectNode mailbox = base("mailbox");
        ((ObjectNode) mailbox.get("native_receipt")).put("query_sequence", true);
        JsonNode check = StrictJson.parse(ArmyInventoryValidation.validate(bytes(mailbox)));
        assertEquals("mailbox_source_or_frame_mismatch", check.get("reason").textValue());
    }

    @Test void sourceBuildGuardStillRejectsCurrentVersionCandidate() throws IOException {
        ObjectNode mailbox = base("mailbox");
        ((ObjectNode) mailbox.get("native_receipt")).put("source_build", "CK3 1.20.0.4");
        JsonNode check = StrictJson.parse(ArmyInventoryValidation.validate(bytes(mailbox)));
        assertEquals("source_build_mismatch", check.get("reason").textValue());
        assertFalse(check.get("date_or_action_authorized").booleanValue());
    }

    @Test void typedResultsCannotFabricateSuccessOrUnsortedEvidence() {
        assertThrows(ContractViolationException.class, () -> new Check(true, Reason.SOURCE_BUILD_MISMATCH, List.of(), List.of()));
        assertThrows(ContractViolationException.class, () -> new Check(true, Reason.SHAPE_VALID_ONLY,
                List.of(BigInteger.TWO, BigInteger.ONE), List.of(BigInteger.ONE)));
        assertThrows(ContractViolationException.class, () -> new Check(false, Reason.SOURCE_BUILD_MISMATCH,
                List.of(BigInteger.ONE), List.of()));
    }
}
