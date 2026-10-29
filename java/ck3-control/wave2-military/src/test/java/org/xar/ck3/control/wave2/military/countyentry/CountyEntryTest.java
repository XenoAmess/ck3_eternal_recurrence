package org.xar.ck3.control.wave2.military.countyentry;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.military.countyentry.CountyEntryRiskModel.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

class CountyEntryTest {
    private JsonNode golden() throws IOException {
        try (var stream = getClass().getResourceAsStream("/countyentry/original-producer-golden.json")) {
            assertNotNull(stream, "actual original producer capture must be present; no skipped golden test");
            return StrictJson.parse(stream.readAllBytes(), 90_112);
        }
    }
    @Test void originalProducerToBothConsumersAndSerializationRoundtrip() throws IOException {
        JsonNode vectors = golden(); assertEquals(18, vectors.get("original_tests").intValue()); assertEquals(43, vectors.get("original_subtests").intValue()); assertEquals(0, vectors.get("original_skipped").intValue());
        assertFalse(vectors.get("machine_id").textValue().isBlank()); assertTrue(vectors.get("source_pins").size() >= 9);
        for (JsonNode entry : vectors.get("contract_cases")) {
            Strength strength = CountyEntryCodec.decodeStrength(entry.get("input"));
            assertEquals(entry.get("present").booleanValue(), strength.countyInputs() != null, entry.get("name").textValue());
            if (strength.countyInputs() != null) {
                byte[] encoded = CountyEntryCodec.encode(strength.countyInputs());
                assertEquals(entry.get("expected"), StrictJson.parse(encoded));
                assertEquals(strength.countyInputs(), CountyEntryCodec.decode(encoded, strength.currentSoldiers()));
            }
        }
        for (JsonNode entry : vectors.get("risk_cases")) {
            byte[] actual = CountyEntryCodec.project(StrictJson.canonical(entry.get("input")));
            assertEquals(entry.get("expected"), StrictJson.parse(actual), entry.get("name").textValue());
            JsonNode output = StrictJson.parse(actual); assertFalse(output.get("native_action_executed").booleanValue());
            assertFalse(output.get("actual_county_loss_observed").booleanValue()); assertTrue(output.get("route_overall_safe").isNull());
        }
    }
    @Test void rawFloatBooleanWrongKeyAndWidthFailuresStayRejected() throws IOException {
        ObjectNode input = (ObjectNode) golden().get("contract_cases").get(0).get("input");
        String valid = new String(StrictJson.canonical(input.get("county_entry_inputs_v1")), StandardCharsets.UTF_8);
        for (String raw : List.of(valid.replace("\"current_loss_budget\":137", "\"current_loss_budget\":137.0"),
                valid.replace("\"current_loss_budget\":137", "\"current_loss_budget\":true"),
                valid.replace("\"current_loss_budget\":137", "\"current_loss_budget\":901"),
                valid.replace("\"effective_fraction_raw\":5000", "\"effective_fraction_raw\":9223372036854775808"),
                valid.replace("\"actor_character_id\":33388", "\"actor_character_id\":-1"),
                valid.replace("\"source\":\"native_current_county_entry_inputs\"", "\"source\":\"applied_loss\""),
                valid.replace("\"passes\":true", "\"passes\":1"), valid.replace("\"soldier_scale\":1", "\"soldier_scale\":1.0"),
                valid.replace("\"soldier_scale\":1", "\"soldier_scale\":1,\"applied_loss\":137"),
                valid.replace("\"soldier_scale\":1", "\"soldier_scale\":1,\"soldier_scale\":1"))) {
            assertNotEquals(valid, raw); assertThrows(ContractViolationException.class,
                    () -> CountyEntryCodec.decode(raw.getBytes(StandardCharsets.UTF_8), 900));
        }
        ObjectNode missing = input.get("county_entry_inputs_v1").deepCopy(); missing.remove("condition");
        assertThrows(ContractViolationException.class, () -> CountyEntryCodec.decode(missing, 900));
        ObjectNode childNull = input.get("county_entry_inputs_v1").deepCopy(); childNull.putNull("multiplier_floor_inputs_v1");
        assertThrows(ContractViolationException.class, () -> CountyEntryCodec.decode(childNull, 900));
        ObjectNode unavailable = input.deepCopy(); unavailable.put("status", "unavailable");
        assertThrows(ContractViolationException.class, () -> CountyEntryCodec.decodeStrength(unavailable));
    }
    @Test void sourceJoinRequiresAllThreeCurrentRevisionsAndArmyIdentity() {
        Provenance current = new Provenance("native:9", 7L, 9L);
        RouteContext route = new RouteContext(18, 100, "complete_nonempty", 2, List.of(101, 102));
        QueryFrame frame = new QueryFrame(current, List.of(route));
        assertSame(route, CountyEntryRisk.joinContext(current, frame, 18));
        assertNull(CountyEntryRisk.joinContext(new Provenance("native:9", 8L, 9L), frame, 18));
        assertNull(CountyEntryRisk.joinContext(new Provenance("native:10", 7L, 9L), frame, 18));
        assertNull(CountyEntryRisk.joinContext(new Provenance("native:9", 7L, 10L), frame, 18));
        assertNull(CountyEntryRisk.joinContext(new Provenance(null, 7L, 9L), frame, 18));
        assertNull(CountyEntryRisk.joinContext(current, frame, 19));
    }
    @Test void declaredSdkProjectionAllowsUnrelatedExtensionsButRejectsBooleanIds() throws IOException {
        ObjectNode input = golden().get("contract_cases").get(0).get("input").deepCopy(); input.putObject("future_sdk_extension").put("observation", true);
        assertNotNull(CountyEntryCodec.decodeStrength(input).countyInputs()); input.put("army_id", true);
        assertThrows(ContractViolationException.class, () -> CountyEntryCodec.decodeStrength(input));
    }
    @Test void unsignedPrefixSubjectDoesNotBecomeSignedArmyIdentity() throws IOException {
        JsonNode entry = golden().get("risk_cases").get(0).get("input");
        Strength original = CountyEntryCodec.decodeStrength(entry.get("strength"));
        Strength signed = new Strength(original.available(), original.armyId(), -1, original.currentSoldiers(), original.countyInputs(), original.lossPartition());
        MovementPrefix prefix = new MovementPrefix(true, 18L, 0xffff_ffffL, 0L);
        Risk risk = CountyEntryRisk.project(signed, CountyEntryCodec.decodeRouteContext(entry.get("army_context")), prefix,
                CountyEntryCodec.decodeMovementOperands(entry.get("strength").get("current_movement_progress")), new PrestoreCall(true, null));
        assertNull(risk.priorUnit170()); assertNull(risk.edgePositive());
        assertEquals(0xffff_ffffL, CountyEntryCodec.decodeMovementPrefix(StrictJson.parse(
                "{\"movement_prefix_input_ready\":true,\"subject_army_id_u32\":18,\"subject_carmy_id_u32\":4294967295,\"conditional_unit_170_raw_after_next_new_date_entry_prefix\":0}"
                        .getBytes(StandardCharsets.UTF_8))).nativeCarmyId().longValue());
    }
}
