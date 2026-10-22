package org.xar.ck3.control.military.battleretreat;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.Recommendation;
import org.xar.ck3.control.military.battleretreat.BattleRetreatPolicy.Request;

final class BattleRetreatPolicyTest {
    private static JsonNode golden() throws IOException {
        try (InputStream input = BattleRetreatPolicyTest.class.getResourceAsStream("/battleretreat/current-retreat-golden.json")) {
            assertNotNull(input, "committed original producer golden is required");
            byte[] raw = input.readNBytes(170_000);
            assertEquals(-1, input.read(), "golden fixture exceeds lane budget");
            return new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
                    .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
                    .readTree(raw);
        }
    }

    private static ObjectNode base() throws IOException {
        return golden().get("cases").get(0).get("input").deepCopy();
    }

    @TestFactory
    Stream<DynamicTest> originalProducerGoldenAndSerializationRoundTrip() throws IOException {
        JsonNode fixture = golden();
        assertEquals(2, fixture.get("original_policy_test_count").intValue());
        assertFalse(fixture.get("native_or_game_execution").booleanValue());
        assertEquals(32, fixture.get("cases").size());
        List<DynamicTest> tests = new ArrayList<>();
        for (JsonNode vector : fixture.get("cases")) {
            tests.add(DynamicTest.dynamicTest(vector.get("name").textValue(), () -> {
                Request request = BattleRetreatCodec.decode(StrictJson.canonical(vector.get("input")));
                assertEquals(request, BattleRetreatCodec.decode(BattleRetreatCodec.encodeRequest(request)));
                assertEquals(vector.get("expected"), StrictJson.parse(BattleRetreatCodec.encodeDecision(BattleRetreatPolicy.assess(request))));
            }));
        }
        return tests.stream();
    }

    @Test
    void rejectsWrongNumericTypesAndOverflowBeforeConstructingDomain() throws IOException {
        for (String replacement : List.of("true", "1.0", "\"1\"", "null", "-1")) {
            ObjectNode value = base();
            value.set("maximum_next_tick_hard_loss_raw", StrictJson.parse(replacement.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> BattleRetreatCodec.decodeNode(value));
        }
        for (String replacement : List.of("true", "5.0", "\"5\"", "0", "18446744073709551616")) {
            ObjectNode value = base();
            ((ObjectNode) value.get("battle_frame")).set("snapshot_revision", StrictJson.parse(replacement.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> BattleRetreatCodec.decodeNode(value));
        }
        for (String field : List.of("selected_owner_character_id", "selected_public_cunit_id", "combat_id", "phase_day")) {
            ObjectNode value = base();
            ((ObjectNode) value.get("battle_frame")).put(field, new BigInteger("2147483648"));
            assertThrows(IllegalArgumentException.class, () -> BattleRetreatCodec.decodeNode(value));
        }
        ObjectNode value = base();
        ((ObjectNode) value.get("battle_frame")).put("combat_id", -1);
        assertThrows(IllegalArgumentException.class, () -> BattleRetreatCodec.decodeNode(value));
        ObjectNode hard = (ObjectNode) base().get("frozen_main_tick").get("sides").get(0).get("losses").get("owner_hard_ledger_deltas").get(0);
        hard.put("hard_casualties_raw_delta", true);
        ObjectNode withBadHard = base();
        ((ObjectNode) withBadHard.get("frozen_main_tick").get("sides").get(0).get("losses").get("owner_hard_ledger_deltas").get(0))
                .set("hard_casualties_raw_delta", hard.get("hard_casualties_raw_delta"));
        assertThrows(IllegalArgumentException.class, () -> BattleRetreatCodec.decodeNode(withBadHard));
    }

    @Test
    void distinguishesMissingNullAndEmptyAndRejectsUnknownAndDuplicateFields() throws IOException {
        ObjectNode value = base(); value.remove("frozen_main_tick");
        assertThrows(IllegalArgumentException.class, () -> BattleRetreatCodec.decodeNode(value));
        ObjectNode nullTick = base(); nullTick.putNull("frozen_main_tick");
        assertEquals(List.of("same_frame_frozen_main_tick"), BattleRetreatPolicy.assess(BattleRetreatCodec.decodeNode(nullTick)).requiredInputs());
        ObjectNode emptyTick = base(); emptyTick.putObject("frozen_main_tick");
        assertThrows(IllegalArgumentException.class, () -> BattleRetreatCodec.decodeNode(emptyTick));
        ObjectNode unknown = base(); unknown.put("unexpected", 1);
        assertThrows(IllegalArgumentException.class, () -> BattleRetreatCodec.decodeNode(unknown));
        ObjectNode nestedUnknown = base(); ((ObjectNode) nestedUnknown.get("retreat_preview").get("source_binding")).put("unbound_revision", 7);
        assertThrows(IllegalArgumentException.class, () -> BattleRetreatCodec.decodeNode(nestedUnknown));
        byte[] duplicate = "{\"schema\":1,\"schema\":1}".getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> BattleRetreatCodec.decode(duplicate));
        assertThrows(IllegalArgumentException.class, () -> BattleRetreatCodec.decode(new byte[] {(byte) 0xc3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> BattleRetreatCodec.decode(new byte[65_537]));
    }

    @Test
    void eachOfEightTickIdentityFieldsRequiresRecomputation() throws IOException {
        for (String field : List.of("snapshot_revision", "observed_date_raw", "combat_id", "province_id",
                "subject_side_index", "phase", "phase_raw", "phase_day")) {
            ObjectNode value = base();
            ObjectNode frame = (ObjectNode) value.get("frozen_main_tick").get("observed_frame");
            if (field.equals("phase")) { frame.put(field, "maneuver"); }
            else { frame.put(field, frame.get(field).bigIntegerValue().add(BigInteger.ONE)); }
            var decision = BattleRetreatPolicy.assess(BattleRetreatCodec.decodeNode(value));
            assertEquals(Recommendation.QUERY_CURRENT_BATTLE_INPUTS, decision.recommendation(), field);
            assertEquals(List.of("frozen_main_tick_from_this_current_frame"), decision.requiredInputs(), field);
        }
    }

    @Test
    void eachOfTenPreviewObservedFieldsPreventsReusingToken() throws IOException {
        for (String field : List.of("snapshot_revision", "observed_date_raw", "combat_id", "province_id",
                "side_index", "selected_public_cunit_id", "selected_owner_character_id", "phase", "phase_day", "side_scope")) {
            ObjectNode value = base();
            ObjectNode frame = (ObjectNode) value.get("retreat_preview").get("battle_control_snapshot");
            if (field.equals("phase")) { frame.put(field, "maneuver"); }
            else if (field.equals("side_scope")) { frame.put(field, "owner_subset"); }
            else { frame.put(field, frame.get(field).bigIntegerValue().add(BigInteger.ONE)); }
            var decision = BattleRetreatPolicy.assess(BattleRetreatCodec.decodeNode(value));
            assertEquals(Recommendation.QUERY_RETREAT_PREVIEW, decision.recommendation(), field);
            assertEquals("recompute_frozen_tick_from_preview_current_battle_frame", decision.reason(), field);
            assertEquals(null, decision.retreatOrderArguments(), field);
        }
    }

    @Test
    void availablePreviewCannotOmitTokenAndNeverProvesTransitionOrDestinationSafety() throws IOException {
        ObjectNode value = base(); ((ObjectNode) value.get("retreat_preview").get("target_preview")).putNull("candidate_token");
        assertThrows(IllegalArgumentException.class, () -> BattleRetreatCodec.decodeNode(value));
        JsonNode output = StrictJson.parse(BattleRetreatCodec.encodeDecision(BattleRetreatPolicy.assess(BattleRetreatCodec.decodeNode(base()))));
        assertFalse(output.get("complete_transition").booleanValue());
        assertFalse(output.get("retreat_destination_safety_observed").booleanValue());
        assertEquals(true, output.get("win_probability").isNull());
        assertEquals(true, output.get("retreat_loss_raw").isNull());
    }
}
