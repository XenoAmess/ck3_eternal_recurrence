package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.core.JsonPointer;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.BooleanNode;
import com.fasterxml.jackson.databind.node.DecimalNode;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.TextNode;
import java.io.InputStream;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;

/** Source-shaped synthetic vectors. These tests grant no Native or saved-day credit. */
class BattleTerminalPersonCodecTest {
    private static final String PERSON = "/0/current_person_state";
    private static final String RAW = PERSON + "/raw_numeric_inputs";
    private static ArrayNode fixture() throws Exception {
        try (InputStream input = BattleTerminalPersonCodecTest.class.getResourceAsStream("/battle-terminal-person-current-source-shaped.json")) {
            assertNotNull(input, "required source-shaped fixture must be materialized");
            return assertInstanceOf(ArrayNode.class, StrictJson.parse(input.readAllBytes()));
        }
    }
    private static JsonNode parse(String raw) { return StrictJson.parse(raw.getBytes(StandardCharsets.UTF_8)); }
    private static ObjectNode object(JsonNode root, String pointer) { return assertInstanceOf(ObjectNode.class, root.at(pointer)); }
    private static JsonNode normalize(JsonNode rows) { return BattleTerminalPersonCodec.normalizeCustody(rows, "character_observations", true); }
    private static void set(JsonNode root, String pointer, JsonNode value) {
        JsonPointer path = JsonPointer.compile(pointer); JsonNode parent = root.at(path.head());
        if (parent instanceof ObjectNode row) row.set(path.last().getMatchingProperty(), value);
        else assertInstanceOf(ArrayNode.class, parent).set(path.last().getMatchingIndex(), value);
    }
    @Test void completeSyntheticCurrentObservationPreservesExactNativeDomainsAndIndependentArrays() throws Exception {
        ArrayNode original = fixture(); JsonNode normalized = normalize(original);
        assertEquals(original, normalized);
        byte[] wire = StrictJson.canonical(normalized);
        assertEquals(normalized, normalize(StrictJson.parse(wire)));
        assertArrayEquals(wire, StrictJson.canonical(normalize(StrictJson.parse(wire))));
        assertEquals(StrictJson.UINT64_MAX, normalized.at(PERSON + "/death_record/date_object_raw_u64").bigIntegerValue());
        assertEquals(2, normalized.at(PERSON + "/current_stored_context_state/key_array/count").intValue());
        assertEquals(3, normalized.at(PERSON + "/current_stored_context_state/value_array/count").intValue());
        object(original, PERSON + "/effective_prowess").put("points", 99);
        assertEquals(0, normalized.at(PERSON + "/effective_prowess/points").intValue());
        assertTrue(BattleTerminalPersonCodec.normalizeCustody(null, "absent", true).isNull());
        assertTrue(BattleTerminalPersonCodec.normalizeCustody(NullNode.instance, "explicit_null", true).isNull());
        assertTrue(BattleTerminalPersonCodec.normalizeCustody(parse("[]"), "empty", true).isEmpty());
    }
    private static void integerPaths(JsonNode value, String path, List<String> target) {
        if (value.isIntegralNumber()) target.add(path);
        else if (value instanceof ObjectNode object) object.properties().forEach(entry -> integerPaths(entry.getValue(), path + "/" + entry.getKey(), target));
        else if (value.isArray()) for (int index = 0; index < value.size(); index++) integerPaths(value.get(index), path + "/" + index, target);
    }
    @Test void everyNestedIntegerRejectsBooleanFloatAndStringAtTheActualCustodyIngress() throws Exception {
        ArrayNode original = fixture(); List<String> paths = new ArrayList<>(); integerPaths(original, "", paths);
        assertTrue(paths.size() > 50, "fixture must cover all nested native domains");
        for (String path : paths) for (JsonNode wrong : List.of(BooleanNode.TRUE, DecimalNode.valueOf(new BigDecimal("1.0")), TextNode.valueOf(original.at(path).asText()))) {
            ArrayNode changed = original.deepCopy(); set(changed, path, wrong);
            assertThrows(IllegalArgumentException.class, () -> normalize(changed), path + ": " + wrong);
        }
    }
    @Test void requiredFieldsUnknownAliasesAndCustodyPermissionAreClosed() throws Exception {
        for (String path : List.of("/0/character_id", PERSON + "/scope", PERSON + "/effective_prowess/points", PERSON + "/injury_traits/flags/wounded_3",
                RAW + "/base_points", RAW + "/context/weighted_count", PERSON + "/current_stored_context_state/reset_input/weighted_count_nonzero")) {
            ArrayNode rows = fixture(); JsonPointer pointer = JsonPointer.compile(path);
            object(rows, pointer.head().toString()).remove(pointer.last().getMatchingProperty());
            assertThrows(IllegalArgumentException.class, () -> normalize(rows), path);
        }
        for (String path : List.of("/0", PERSON, PERSON + "/effective_prowess", PERSON + "/injury_traits/flags", RAW,
                RAW + "/context/aggregate_properties", PERSON + "/current_prior_context_inputs/selector", PERSON + "/current_stored_context_state/key_array")) {
            ArrayNode rows = fixture(); object(rows, path).put("unknown_alias", 1);
            assertThrows(IllegalArgumentException.class, () -> normalize(rows), path);
        }
        ArrayNode rows = fixture(); assertThrows(IllegalArgumentException.class,
                () -> BattleTerminalPersonCodec.normalizeCustody(rows, "prior.character_custody", false));
        for (String status : List.of("none", "observed", "unavailable")) {
            ArrayNode changed = fixture(); object(changed, "/0").put("status", status).put("actual_jailer_character_id", 0);
            assertThrows(IllegalArgumentException.class, () -> normalize(changed), status);
        }
    }
    @Test void everyNestedReceiverMustMatchTheEnclosingCharacterWithoutRewritingIt() throws Exception {
        for (String path : List.of(RAW + "/character_id", PERSON + "/context_branch_inputs/character_id", PERSON + "/context_branch_inputs/census_inputs/character_id",
                PERSON + "/current_prior_context_inputs/character_full_id", PERSON + "/current_stored_context_state/character_full_id")) {
            ArrayNode changed = fixture(); set(changed, path, parse("30111"));
            assertThrows(IllegalArgumentException.class, () -> normalize(changed), path);
        }
    }
    @Test void optionalAbsenceExplicitNullAndKnownEmptyRemainDistinctWithoutInventingPersonState() throws Exception {
        ArrayNode absent = fixture(); object(absent, PERSON).remove("raw_numeric_inputs");
        JsonNode normalizedAbsent = normalize(absent); assertFalse(normalizedAbsent.at(PERSON).has("raw_numeric_inputs"));
        ArrayNode explicitNull = fixture(); object(explicitNull, PERSON).putNull("raw_numeric_inputs");
        JsonNode normalizedNull = normalize(explicitNull); assertTrue(normalizedNull.at(RAW).isNull());
        assertNotEquals(normalizedAbsent, normalizedNull);
        ArrayNode noAlive = fixture(); object(noAlive, "/0").remove("alive"); assertFalse(normalize(noAlive).get(0).has("alive"));
        ArrayNode unknownAlive = fixture(); object(unknownAlive, "/0").putNull("alive"); assertTrue(normalize(unknownAlive).get(0).get("alive").isNull());
        ArrayNode nullPerson = fixture(); object(nullPerson, "/0").putNull("current_person_state");
        assertThrows(IllegalArgumentException.class, () -> normalize(nullPerson));
    }
    @Test void titleCensusConsumesOnlyDemandedQualifiersAndBranchReadinessRemainsIndependent() throws Exception {
        ArrayNode rows = fixture(); ObjectNode census = object(rows, PERSON + "/context_branch_inputs/census_inputs");
        census.put("title_count_raw_i32", 1).set("title_occurrences", parse("""
                [{"native_row_index":0,"requested_full_title_id_raw_i32":-2147483648,"resolution":"matched",
                  "resolved_full_title_id_raw_i32":-2147483648,"qualifier_1d8_raw_u8":1,"qualifier_130_raw_u8":null,
                  "qualifier_12c_raw_i32":null,"government_bit14":null,"template_tier_raw_i32":null}]
                """));
        assertEquals(rows, normalize(rows));
        object(rows, PERSON + "/context_branch_inputs/census_inputs/title_occurrences/0").putNull("qualifier_1d8_raw_u8");
        assertThrows(IllegalArgumentException.class, () -> normalize(rows));
        ArrayNode groups = fixture(); assertInstanceOf(ArrayNode.class, groups.at(PERSON + "/context_branch_inputs/group_counts")).set(0, parse("1"));
        assertThrows(IllegalArgumentException.class, () -> normalize(groups));
    }
    @Test void rawAvailabilityAuxiliaryThresholdAndNineCacheBranchesRetainTheOriginalGuards() throws Exception {
        ArrayNode rows = fixture(); ObjectNode raw = object(rows, RAW);
        raw.set("auxiliary_scratch_inputs", parse("""
                {"status":"available","ready":true,"base430_q64":0,"base438_q64":0,"selector_flag_raw":0,
                 "selector_metric_raw":-1,"selected_low_threshold_raw":0,"selected_high_threshold_raw":null,
                 "prepared430_q64":0,"prepared438_q64":0,"copied430_q64":0,"copied438_q64":0,"ready440_raw":0,"unavailable_reason":null}
                """));
        raw.set("nine_cache_byte_inputs", parse("""
                {"status":"available","ready":true,"model_present":true,"aggregate_properties":{"count":0,"keys_u16":[],"values_q64":[]},
                 "carrier278_present":true,"carrier278_magic_raw":0,"linked20_present":null,"used_native_definition_fallback":null,
                 "selected_definition_present":null,"selected_definition_magic_raw":null,"selected_definition_keys_u16":null,
                 "current_cache_present":null,"current_cache_bytes":null,"unavailable_reason":null}
                """));
        assertEquals(rows, normalize(rows));
        object(rows, RAW + "/auxiliary_scratch_inputs").put("selector_metric_raw", 0);
        assertThrows(IllegalArgumentException.class, () -> normalize(rows));
        object(rows, RAW + "/auxiliary_scratch_inputs").put("selected_high_threshold_raw", 1);
        object(rows, RAW + "/nine_cache_byte_inputs").put("carrier278_magic_raw", 0x41495374L);
        assertThrows(IllegalArgumentException.class, () -> normalize(rows));
        object(rows, RAW + "/nine_cache_byte_inputs").put("linked20_present", false).put("used_native_definition_fallback", true)
                .put("selected_definition_present", true).put("selected_definition_magic_raw", 0);
        assertEquals(rows, normalize(rows));
    }
    @Test void storedNegativeAndUnequalDescriptorsAreObservationsRatherThanInventedReadyContexts() throws Exception {
        ArrayNode rows = fixture(); ObjectNode state = object(rows, PERSON + "/current_stored_context_state");
        state.put("available", false).put("reason", "negative_weighted_active_extent");
        state.set("weighted", parse("{\"data_address\":24576,\"capacity_raw\":4,\"count\":-3,\"items\":null}"));
        object(rows, PERSON + "/current_stored_context_state/reset_input").put("weighted_count_nonzero", true);
        assertEquals(rows, normalize(rows));
        object(rows, PERSON + "/current_stored_context_state/weighted").putArray("items");
        assertThrows(IllegalArgumentException.class, () -> normalize(rows));
        ArrayNode prefix = fixture(); object(prefix, PERSON + "/current_prior_context_inputs/selector").put("selected_header_offset", 0x18f8);
        assertThrows(IllegalArgumentException.class, () -> normalize(prefix));
    }
    @Test void injuryRankAndDeathOptionalMetadataNeverBorrowAvailabilityFromAnotherLeaf() throws Exception {
        ArrayNode rows = fixture(); ObjectNode injury = object(rows, PERSON + "/injury_traits");
        object(rows, PERSON + "/injury_traits/flags").put("wounded_1", true).put("wounded_2", true);
        injury.putNull("wounded_rank").put("wounded_rank_unavailable_reason", "multiple_native_flags");
        assertEquals(rows, normalize(rows));
        injury.put("wounded_rank", 2); assertThrows(IllegalArgumentException.class, () -> normalize(rows));
        for (JsonNode wrong : List.of(TextNode.valueOf("18446744073709551615"), parse("18446744073709551616"), BooleanNode.TRUE)) {
            ArrayNode changed = fixture(); set(changed, PERSON + "/death_record/date_object_raw_u64", wrong);
            assertThrows(IllegalArgumentException.class, () -> normalize(changed));
        }
    }
    @Test void pendingQueueRetainsObservedRowIndexAndExactU64WithoutInferringCommitOrCountAgreement() {
        JsonNode queue = parse("""
                {"status":"available","unavailable_reason":null,"source_state_pointer_present":true,"manager_owner_pointer_present":true,
                 "execution_mode_raw":255,"data_pointer_present":true,"capacity_raw":-1,"count_raw":-2,
                 "rows":[{"status":"available","unavailable_reason":null,"row_index":99,"victim_pointer_present":true,
                  "victim_full_character_id_raw":-1,"victim_death_data_pointer_present":true,"reason_pointer_present":true,"reason_key":"",
                  "date_object_raw_u64":18446744073709551615,"killer_pointer_present":null,"killer_full_character_id_raw":null,
                  "artifact_pointer_present":false,"artifact_full_id_raw":-2147483648}]}
                """);
        JsonNode normalized = BattleTerminalPersonCodec.normalizePendingDeathQueue(queue);
        assertEquals(queue, normalized);
        assertEquals(normalized, BattleTerminalPersonCodec.normalizePendingDeathQueue(StrictJson.parse(StrictJson.canonical(normalized))));
        ObjectNode changed = assertInstanceOf(ObjectNode.class, queue.deepCopy());
        object(changed, "/rows/0").put("row_index", true);
        assertThrows(IllegalArgumentException.class, () -> BattleTerminalPersonCodec.normalizePendingDeathQueue(changed));
        assertTrue(BattleTerminalPersonCodec.normalizePendingDeathQueue(NullNode.instance).isNull());
    }
    @Test void originalExternalWireNamesHaveExactlyOneTypedEnumAndUnknownKeysCannotBeDispatched() {
        var names = new HashSet<String>();
        assertEquals(33, BattlePersonExternalCodec.Leaf.values().length);
        for (var leaf : BattlePersonExternalCodec.Leaf.values()) {
            assertTrue(names.add(leaf.wire())); assertSame(leaf, BattlePersonExternalCodec.Leaf.fromWire(leaf.wire()));
        }
        for (String wrong : List.of("", "unknown", "FOLLOWING_2921A90", "following_2921a90 "))
            assertThrows(IllegalArgumentException.class, () -> BattlePersonExternalCodec.Leaf.fromWire(wrong));
    }
}
