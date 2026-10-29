package org.xar.ck3.control.wave2.military.holyreinf;

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

final class HolyReinforcementTest {
    private static final int BUDGET = HolyReinforcementCodec.BYTE_BUDGET;
    private static JsonNode golden() throws IOException {
        try (var stream = HolyReinforcementTest.class.getResourceAsStream("/holyreinf/golden.json.gz")) {
            assertNotNull(stream, "real old-producer golden must be captured by the unified execution owner; no skip/fallback");
            JsonNode value;
            try (var gzip = new GZIPInputStream(stream)) { value = StrictJson.parse(gzip.readNBytes(262_145), 262_144); }
            assertEquals("xar.ck3.holy-reinforcement-golden.v1", value.path("schema").textValue());
            assertFalse(value.path("machine_id").asText().isBlank()); assertNotEquals("unknown", value.path("machine_id").asText());
            assertTrue(value.path("original_tests").intValue() > 0); assertEquals(0, value.path("original_skipped").intValue());
            assertTrue(value.path("actual_production_functions").booleanValue());
            assertTrue(value.path("synthetic_world_and_callback_outcomes").booleanValue());
            assertTrue(value.path("source_pins").size() >= 9);
            for (JsonNode pin : value.path("source_pins")) { assertTrue(pin.path("sha256").asText().matches("[0-9a-f]{64}")); }
            return value;
        }
    }
    @TestFactory List<DynamicTest> originalProducerToEveryConsumerAndRoundTrip() throws IOException {
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode row : golden().path("cases")) {
            tests.add(DynamicTest.dynamicTest(row.path("name").asText(), () -> {
                byte[] request = StrictJson.canonical(row.get("input"), BUDGET);
                byte[] actual = switch (row.path("operation").asText()) {
                    case "choose" -> HolyReinforcementCodec.choose(request);
                    case "plan" -> HolyReinforcementCodec.plan(request);
                    case "post" -> HolyReinforcementCodec.postcondition(request);
                    default -> throw new IllegalArgumentException("unknown captured operation");
                };
                JsonNode parsed = StrictJson.parse(actual, BUDGET);
                assertEquals(row.get("expected"), parsed);
                assertArrayEquals(actual, StrictJson.canonical(parsed, BUDGET));
                if (row.path("operation").asText().equals("post")) {
                    assertFalse(parsed.path("holy_order_reinforcement_postcondition").path("full_hire_loop_complete").booleanValue());
                    assertFalse(parsed.path("holy_order_hire").path("after_state_observed").booleanValue());
                }
            }));
        }
        assertTrue(tests.size() >= 29, "all real comparison branches must be captured"); return tests;
    }
    private static ObjectNode first(String name) throws IOException {
        for (JsonNode row : golden().path("cases")) { if (row.path("name").asText().equals(name)) { return (ObjectNode) row.get("input").deepCopy(); } }
        throw new IllegalArgumentException("captured case not found: " + name);
    }
    private static ObjectNode terms(ObjectNode input) { return (ObjectNode) input.path("holy_context").path("rows").get(0).path("military_terms"); }
    private static void rejects(ObjectNode input) {
        assertThrows(IllegalArgumentException.class, () -> HolyReinforcementCodec.choose(StrictJson.canonical(input, BUDGET)));
    }
    @Test void rejectsExactIntegerSubstitutesAtRawTokenBoundary() throws IOException {
        String raw = new String(StrictJson.canonical(first("current-native-zero-reference"), BUDGET), StandardCharsets.UTF_8);
        for (String token : List.of("true", "0.0", "\"0\"", "4294967296", "-1")) {
            String mutated = raw.replace("\"holy_order_id\":0", "\"holy_order_id\":" + token);
            assertNotEquals(raw, mutated); assertThrows(IllegalArgumentException.class,
                    () -> HolyReinforcementCodec.choose(mutated.getBytes(StandardCharsets.UTF_8)), token);
        }
        assertThrows(IllegalArgumentException.class, () -> HolyReinforcementCodec.choose(raw.replace("\"capture_epoch\":110", "\"capture_epoch\":110.0").getBytes(StandardCharsets.UTF_8)));
    }
    @Test void exactOuterFieldsAndAdditiveSdkContainers() throws IOException {
        ObjectNode input = first("current-native-zero-reference"); input.put("unexpected", 1); rejects(input); input.remove("unexpected");
        JsonNode expected = StrictJson.parse(HolyReinforcementCodec.choose(StrictJson.canonical(input, BUDGET)), BUDGET);
        ((ObjectNode) input.get("snapshot")).put("future_sdk_observer", "additive"); terms(input).put("future_native_terms", 1);
        assertEquals(expected, StrictJson.parse(HolyReinforcementCodec.choose(StrictJson.canonical(input, BUDGET)), BUDGET));
        terms(input).remove("can_hire_reasons_available"); rejects(input);
    }
    @Test void unavailableMissingAndNullStrengthRemainDistinct() throws IOException {
        ObjectNode input = first("current-native-zero-reference"); terms(input).putNull("troop_strength"); rejects(input);
        terms(input).remove("troop_strength");
        JsonNode result = StrictJson.parse(HolyReinforcementCodec.choose(StrictJson.canonical(input, BUDGET)), BUDGET);
        assertEquals("current_soldiers_unavailable", result.path("candidate_rows").get(0).path("reason").asText());
        assertTrue(result.get("selected_step").isNull());
    }
    @Test void validatesEveryAdditiveObserverWithoutGrantingNativeEligibility() throws IOException {
        ObjectNode input = first("additive-observers-do-not-replace-final-predicates");
        ObjectNode cost = (ObjectNode) terms(input).get("hire_cost_context"); cost.put("patron_is_player", true); rejects(input);
        input = first("additive-observers-do-not-replace-final-predicates");
        ((ObjectNode) terms(input).get("current_war_eligibility")).putNull("reason_literal"); rejects(input);
        input = first("additive-observers-do-not-replace-final-predicates");
        ((ObjectNode) terms(input).get("service_lifecycle")).put("applies_to_player", true); rejects(input);
        input = first("additive-observers-do-not-replace-final-predicates");
        ((ObjectNode) terms(input).get("current_reinforcement_v1")).put("source_count", true); rejects(input);
        input = first("current-native-zero-reference"); ((ObjectNode) input.path("holy_context")).put("queried_revision", 11); rejects(input);
        input = first("current-native-zero-reference"); ((ObjectNode) input.path("holy_context")).put("executable_sha256", "0".repeat(64)); rejects(input);
    }
    @Test void materialObservationDoesNotGrantArrivalVictoryOrFullLoop() throws IOException {
        ObjectNode input = first("ack-and-independent-material-army");
        JsonNode output = StrictJson.parse(HolyReinforcementCodec.postcondition(StrictJson.canonical(input, BUDGET)), BUDGET);
        JsonNode receipt = output.path("holy_order_reinforcement_postcondition");
        assertTrue(receipt.path("employer_observed").booleanValue()); assertTrue(receipt.path("usable_army_observed").booleanValue());
        assertFalse(receipt.path("full_hire_loop_complete").booleanValue()); assertFalse(receipt.has("arrival_observed")); assertFalse(receipt.has("battle_win_probability"));
        assertEquals(0, receipt.path("material_armies").get(0).path("native_carmy_id").longValue());
        assertEquals(4444, receipt.path("material_armies").get(0).path("owner_character_id").longValue());
        assertTrue(receipt.path("next_formal").path("selected_step").asText().startsWith("preview-move-army-"));
    }
}
