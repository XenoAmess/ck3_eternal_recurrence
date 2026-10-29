package org.xar.ck3.control.wave3.governance.betrothalvalue;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.*;
import static org.xar.ck3.control.wave3.governance.betrothalvalue.BetrothalValueModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalCodec;

class BetrothalValuePolicyTest {
    private static JsonNode golden() throws IOException {
        try (InputStream input = BetrothalValuePolicyTest.class.getResourceAsStream("/betrothalvalue/python-golden-v1.json")) {
            assertNotNull(input, "actual original producer golden is required; no default Python fallback");
            JsonNode golden = BetrothalCodec.readJson(input.readAllBytes());
            assertEquals("xar.ck3.betrothal-value-python-golden.v1", golden.path("schema").textValue());
            assertEquals(14, golden.path("original_tests_run").intValue());
            assertEquals(0, golden.path("original_failures").intValue());
            assertEquals(0, golden.path("original_errors").intValue());
            assertEquals(0, golden.path("original_skipped").intValue());
            assertTrue(golden.path("cases").size() >= 40);
            assertEquals(6, golden.path("native_action_cases").size());
            assertEquals(9, golden.path("source_refs").size());
            assertEquals(10, golden.path("input_refs").size());
            return golden;
        }
    }
    private static JsonNode patched(JsonNode base, JsonNode patches) {
        JsonNode result = base.deepCopy();
        for (JsonNode patch : patches) {
            JsonNode path = patch.get("path");
            if (path.isEmpty()) { result = patch.get("value").deepCopy(); continue; }
            JsonNode parent = result;
            for (int i = 0; i < path.size() - 1; i++) { JsonNode key = path.get(i); parent = key.isIntegralNumber() ? parent.get(key.intValue()) : parent.get(key.textValue()); }
            JsonNode key = path.get(path.size() - 1);
            if (parent instanceof ObjectNode object) {
                if (patch.path("remove").asBoolean()) { object.remove(key.textValue()); } else { object.set(key.textValue(), patch.get("value").deepCopy()); }
            } else if (parent instanceof ArrayNode array) {
                if (patch.path("remove").asBoolean()) { array.remove(key.intValue()); } else { array.set(key.intValue(), patch.get("value").deepCopy()); }
            } else { fail("invalid committed patch path"); }
        }
        return result;
    }
    private static byte[] bytes(JsonNode node) { return BetrothalCodec.encodeEvidence(BetrothalCodec.projectEvidence(node)); }
    private static Choice evaluate(JsonNode request) { return BetrothalValuePolicy.evaluate(BetrothalValueCodec.decode(bytes(request))); }
    private static byte[] rawToken(ObjectNode request, ObjectNode owner, String key, String token) {
        owner.put(key, "__value_raw_token__");
        String raw = request.toString(); String marker = "\"__value_raw_token__\"";
        int at = raw.indexOf(marker); assertTrue(at >= 0); assertEquals(at, raw.lastIndexOf(marker));
        raw = raw.substring(0, at) + token + raw.substring(at + marker.length());
        assertTrue(raw.contains("\"" + key + "\":" + token), "outbound token must not pass through BigDecimal tree normalization");
        assertFalse(raw.contains(marker)); return raw.getBytes(StandardCharsets.UTF_8);
    }

    @Test
    void fullOriginalEvaluatorAndReasonOrderMatch() throws IOException {
        JsonNode golden = golden();
        for (JsonNode row : golden.get("cases")) {
            JsonNode request = patched(golden.get("base_request"), row.get("patches"));
            String name = row.get("name").textValue();
            if (row.path("expected_error").asBoolean()) { assertThrows(IllegalArgumentException.class, () -> evaluate(request), name); }
            else {
                Choice choice = evaluate(request);
                assertEquals(patched(golden.get("base_expected"), row.get("expected_patches")), BetrothalCodec.readJson(BetrothalValueCodec.encodeChoice(choice)), name);
                assertFalse(choice.resourceProposal().resourceReservationPerformed(), name);
                assertEquals(row.get("expected_provenance"), BetrothalCodec.readJson(BetrothalCodec.encodeEvidence(BetrothalValuePolicy.provenance(BetrothalValueCodec.decode(bytes(request)).snapshot()))), name);
            }
        }
    }

    @Test
    void sixActualNativeProducerPacketsPassTheSameCompleteValidator() throws IOException {
        for (JsonNode row : golden().get("native_action_cases")) {
            Roles roles = new Roles(row.get("actor").bigIntegerValue(), nullableId(row.get("heir")), nullableId(row.get("partner")), null, null);
            ValidatedActionability value = CurrentPairActionabilityValidator.validate(BetrothalCodec.projectEvidence(row.get("input")), roles);
            assertEquals(row.get("expected"), BetrothalCodec.readJson(BetrothalValueCodec.encodeValidatedActionability(value)), row.get("name").textValue());
        }
    }
    private static BigInteger nullableId(JsonNode value) { return value.isNull() ? null : value.bigIntegerValue(); }

    @Test
    void typedInputsAndOpaqueEvidenceRoundTripWithoutLosingMissingOrFloat() throws IOException {
        JsonNode golden = golden();
        for (JsonNode row : golden.get("cases")) {
            if (row.path("expected_error").asBoolean()) { continue; }
            EvaluationInput input = BetrothalValueCodec.decode(bytes(patched(golden.get("base_request"), row.get("patches"))));
            byte[] encoded = BetrothalValueCodec.encode(input);
            assertEquals(input, BetrothalValueCodec.decode(encoded));
            assertArrayEquals(encoded, BetrothalValueCodec.encode(BetrothalValueCodec.decode(encoded)));
        }
        ObjectNode request = (ObjectNode) golden.get("base_request").deepCopy();
        ObjectNode relation = (ObjectNode) request.get("relationship");
        relation.set("current_first_heir_descendants_v1", BetrothalCodec.readJson("{\"opaque\":1.0,\"nested\":[null,[]]}".getBytes(StandardCharsets.UTF_8)));
        EvaluationInput input = BetrothalValueCodec.decode(bytes(request));
        byte[] encoded = BetrothalValueCodec.encode(input);
        assertTrue(BetrothalCodec.readJson(encoded).get("relationship").get("current_first_heir_descendants_v1").get("opaque").isFloatingPointNumber());
        assertEquals(input, BetrothalValueCodec.decode(encoded));
        assertTrue(BetrothalCodec.readJson(BetrothalValueCodec.encodeChoice(BetrothalValuePolicy.evaluate(input)))
                .get("current_first_heir_descendants_v1").get("opaque").isFloatingPointNumber());
    }

    @Test
    void requiredEnvelopeAndAvailableNativeFieldsCannotDisappear() throws IOException {
        ObjectNode base = (ObjectNode) golden().get("base_request");
        for (String key : List.of("schema", "snapshot", "relationship")) {
            ObjectNode request = base.deepCopy(); request.remove(key);
            assertThrows(IllegalArgumentException.class, () -> evaluate(request), key);
        }
        ObjectNode extra = base.deepCopy(); extra.put("native_qualified", true);
        assertThrows(IllegalArgumentException.class, () -> evaluate(extra));
        for (String key : List.of("status", "actor_character_id", "heir_character_id", "partner_character_id", "recipient_character_id",
                "adult_readback_available", "heir_is_adult", "partner_is_adult", "heir_adult_measure_raw", "partner_adult_measure_raw",
                "heir_adult_threshold_raw", "partner_adult_threshold_raw", "ready_to_marry_betrothed", "final_legality_sampled",
                "complete_can_send", "recipient_acceptance_ready", "recipient_ai_accept_raw", "recipient_answer_status_raw", "generic_costs",
                "effective_matrilineal_if_accepted", "predicted_outcome_if_accepted")) {
            ObjectNode request = base.deepCopy(); ((ObjectNode) request.get("relationship").get("betrothal_actionability")).remove(key);
            assertThrows(IllegalArgumentException.class, () -> evaluate(request), key);
        }
    }

    @Test
    void integerAndBooleanTokensAreStrictAtTheActualParser() throws IOException {
        ObjectNode base = (ObjectNode) golden().get("base_request");
        for (String key : List.of("actor_character_id", "heir_adult_measure_raw", "heir_adult_threshold_raw", "recipient_ai_accept_raw", "recipient_answer_status_raw")) {
            for (String token : List.of("true", "false", "1.0", "1e0", "\"1\"", "[]", "{}")) {
                ObjectNode request = base.deepCopy(); ObjectNode owner = (ObjectNode) request.get("relationship").get("betrothal_actionability");
                byte[] raw = rawToken(request, owner, key, token);
                assertThrows(IllegalArgumentException.class, () -> BetrothalValuePolicy.evaluate(BetrothalValueCodec.decode(raw)), key + ":" + token);
            }
        }
        for (String key : List.of("adult_readback_available", "heir_is_adult", "ready_to_marry_betrothed", "complete_can_send", "recipient_acceptance_ready")) {
            for (String token : List.of("0", "1", "\"true\"", "[]", "{}")) {
                ObjectNode request = base.deepCopy(); byte[] raw = rawToken(request, (ObjectNode) request.get("relationship").get("betrothal_actionability"), key, token);
                assertThrows(IllegalArgumentException.class, () -> BetrothalValuePolicy.evaluate(BetrothalValueCodec.decode(raw)), key + ":" + token);
            }
        }
        ObjectNode request = base.deepCopy(); byte[] raw = rawToken(request, (ObjectNode) request.get("relationship").get("betrothal_actionability").get("generic_costs"), "raw_scale", "100000.0");
        assertThrows(IllegalArgumentException.class, () -> BetrothalValuePolicy.evaluate(BetrothalValueCodec.decode(raw)));
    }

    @Test
    void nativeWidthsAndPreviewIdentityStayBound() throws IOException {
        ObjectNode base = (ObjectNode) golden().get("base_request");
        for (String[] row : new String[][] {{"heir_adult_measure_raw", "32768"}, {"heir_adult_measure_raw", "-32769"},
                {"heir_adult_threshold_raw", "2147483648"}, {"heir_adult_threshold_raw", "-2147483649"},
                {"recipient_ai_accept_raw", "9223372036854775808"}, {"recipient_ai_accept_raw", "-9223372036854775809"},
                {"recipient_answer_status_raw", "3"}, {"actor_character_id", "2147483648"}, {"actor_character_id", "0"}}) {
            ObjectNode request = base.deepCopy(); byte[] raw = rawToken(request, (ObjectNode) request.get("relationship").get("betrothal_actionability"), row[0], row[1]);
            assertThrows(IllegalArgumentException.class, () -> BetrothalValuePolicy.evaluate(BetrothalValueCodec.decode(raw)), String.join(":", row));
        }
        for (String token : List.of("9223372036854775807", "-9223372036854775808")) {
            ObjectNode request = base.deepCopy(); byte[] raw = rawToken(request, (ObjectNode) request.get("relationship").get("betrothal_actionability"), "recipient_ai_accept_raw", token);
            Choice choice = BetrothalValuePolicy.evaluate(BetrothalValueCodec.decode(raw));
            assertEquals(new BigInteger(token), choice.value().recipient().acceptanceRaw());
        }
    }

    @Test
    void finalizedPreviewRequiredFieldsAndHouseIdentityTokensAreStrict() throws IOException {
        JsonNode golden = golden(); JsonNode selected = null;
        for (JsonNode row : golden.get("cases")) {
            if ("selected-false-preview".equals(row.get("name").textValue())) { selected = patched(golden.get("base_request"), row.get("patches")); }
        }
        assertNotNull(selected, "actual original preview case is mandatory");
        ObjectNode base = (ObjectNode) selected;
        for (String key : List.of("status", "reason", "subject_character_id", "candidate_character_id", "requested_matrilineal_option",
                "selected_matrilineal_option", "effective_matrilineal_if_accepted", "complete_can_send", "native_selected_parent_character_id")) {
            ObjectNode request = base.deepCopy(); ((ObjectNode) request.get("relationship").get("betrothal_actionability").get("native_child_house_preview")).remove(key);
            assertThrows(IllegalArgumentException.class, () -> evaluate(request), key);
        }
        for (String key : List.of("house_id", "dynasty_id", "native_selected_parent_character_id")) {
            for (String token : List.of("true", "1.0", "1e0", "\"1\"", "2147483648", "-1")) {
                ObjectNode request = base.deepCopy(); ObjectNode preview = (ObjectNode) request.get("relationship").get("betrothal_actionability").get("native_child_house_preview");
                byte[] raw = rawToken(request, preview, key, token);
                assertThrows(IllegalArgumentException.class, () -> BetrothalValuePolicy.evaluate(BetrothalValueCodec.decode(raw)), key + ":" + token);
            }
        }
        ObjectNode request = base.deepCopy(); ObjectNode preview = (ObjectNode) request.get("relationship").get("betrothal_actionability").get("native_child_house_preview");
        preview.put("house_id", Integer.MAX_VALUE); preview.put("dynasty_id", 0);
        assertEquals(BigInteger.valueOf(Integer.MAX_VALUE), evaluate(request).value().preview().houseId());
        preview.remove("house_id"); preview.putNull("dynasty_id");
        assertNull(evaluate(request).value().preview().houseId());
        assertNull(evaluate(request).value().preview().dynastyId());
    }

    @Test
    void parserRejectsDuplicateKeysTrailingJsonInvalidUtf8AndOversize() throws IOException {
        String raw = golden().get("base_request").toString();
        assertThrows(IllegalArgumentException.class, () -> BetrothalValueCodec.decode(("{\"schema\":\"duplicate\"," + raw.substring(1)).getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> BetrothalValueCodec.decode((raw + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> BetrothalValueCodec.decode(new byte[] {(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> BetrothalValueCodec.decode(new byte[BetrothalCodec.MAX_BYTES + 1]));
    }
}
