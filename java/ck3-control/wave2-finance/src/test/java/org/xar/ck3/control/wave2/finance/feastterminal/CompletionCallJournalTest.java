package org.xar.ck3.control.wave2.finance.feastterminal;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.feastterminal.CompletionCallJournal.Journal;
import org.xar.ck3.control.wave2.finance.feastterminal.CompletionCallJournal.Scope;
import org.xar.ck3.control.wave2.finance.feastterminal.CompletionCallJournal.Source;

/** Software contract cases only; no original native callback or game result is manufactured. */
final class CompletionCallJournalTest {
    private static final Source SOURCE = new Source("synthetic-machine", 10, "134000000000000001",
            BigInteger.valueOf(900), 53200001, 40526, CompletionCallJournal.BUILD, CompletionCallJournal.EXE);
    private static final long ACTIVITY = 83887164L;

    @Test void fullWidthFieldsRoundTripAndCounterDeltaNeverGrantPayoff() {
        ObjectNode input = fixture(); ObjectNode after = after(input);
        after.put("completed_raw_u8", 2).put("invalidated_raw_u8", 255);
        after.put("native_completion_stamp_raw_u64", "18446744073709551615");
        after.put("prestige_raw_i64", "110").put("stress_raw_i32", 80);
        Journal read = decode(input); var value = CompletionCallJournal.consume(read, ACTIVITY).getFirst();
        assertEquals(new BigInteger("18446744073709551615"), value.afterNativeFields().orElseThrow().completionStampRaw().orElseThrow());
        assertEquals(2, value.afterNativeFields().orElseThrow().completed().orElseThrow());
        assertEquals(255, value.afterNativeFields().orElseThrow().invalidated().orElseThrow());
        assertEquals(BigInteger.TEN, value.prestigeDeltaRaw().orElseThrow());
        assertEquals(BigInteger.valueOf(-20), value.stressDeltaRaw().orElseThrow());
        assertFalse(value.counterChangesAttributedToFeast()); assertFalse(value.terminalCauseObserved());
        assertFalse(value.benefitVerified()); assertFalse(value.wholeM6Complete());
        Journal roundTrip = CompletionCallJournal.decode(read.copiedJson(), SOURCE);
        assertEquals(read.records().getFirst().after().nativeFields(), roundTrip.records().getFirst().after().nativeFields());
        assertArrayEquals(read.copiedJson(), roundTrip.copiedJson());
    }
    @Test void unreadZeroAndMissingVersionedFieldsRemainDifferent() {
        ObjectNode input = fixture(); ObjectNode face = after(input);
        face.put("completed_observed", false).putNull("completed_raw_u8");
        face.put("native_completion_stamp_observed", false).putNull("native_completion_stamp_raw_u64");
        var fields = CompletionCallJournal.consume(decode(input), ACTIVITY).getFirst().afterNativeFields().orElseThrow();
        assertTrue(fields.completed().isEmpty()); assertEquals(0, fields.invalidated().orElseThrow());
        assertTrue(fields.completionStampRaw().isEmpty());
        ObjectNode old = legacy(fixture());
        assertTrue(CompletionCallJournal.consume(decode(old), ACTIVITY).getFirst().afterNativeFields().isEmpty());
    }
    @Test void reusedStorageAndUnpairedReturnsNeverSupplyChangesOrTerminalFlags() {
        ObjectNode input = fixture(); ObjectNode row = row(input);
        after(input).put("activity_full_id_u32", ACTIVITY + 1);
        row.put("same_activity_full_id", false);
        var value = CompletionCallJournal.consume(decode(input), ACTIVITY).getFirst();
        assertFalse(value.pairedIdentities()); assertTrue(value.prestigeDeltaRaw().isEmpty());
        assertTrue(value.afterNativeFields().isEmpty());
        input = fixture(); row(input).put("original_call_return_observed", false);
        assertTrue(CompletionCallJournal.consume(decode(input), ACTIVITY).getFirst().afterNativeFields().isEmpty());
    }
    @Test void exactSecondIntervalRetainsFollowingNativeCallScope() {
        ObjectNode input = fixture(); ObjectNode row = row(input);
        row.put("source_call_rva_u64", 0x23F6B9A).put("source_return_rva_u64", 0x23F6B9F)
                .put("source_after_cut_rva_u64", 0x23F6BA7).put("intervening_call_rva_u64", 0x23F6BA2)
                .put("intervening_callee_rva_u64", 0x28BEF00)
                .put("observation_scope", "original_completion_call_and_following_native_call");
        assertEquals(Scope.COMPLETION_AND_FOLLOWING_NATIVE_CALL, decode(input).records().getFirst().scope());
        row.put("source_after_cut_rva_u64", 0x23F6B9F);
        assertThrows(IllegalArgumentException.class, () -> decode(input));
    }
    @Test void strictBoundaryRefusesWrongFieldsTypesRangesAndInventedReadability() {
        List<Consumer<ObjectNode>> mutations = List.of(
                value -> after(value).remove("completed_raw_u8"),
                value -> after(value).put("completed_raw_u8", true),
                value -> after(value).put("completed_raw_u8", 1.0),
                value -> after(value).put("completed_raw_u8", 256),
                value -> after(value).put("completed_observed", false),
                value -> after(value).put("native_completion_stamp_raw_u64", "01"),
                value -> after(value).put("native_completion_stamp_raw_u64", "-0"),
                value -> after(value).put("native_completion_stamp_raw_u64", "18446744073709551616"),
                value -> row(value).put("same_activity_full_id", false),
                value -> row(value).put("capture_thread_id_u32", 44),
                value -> value.put("query_actor_full_id_u32", 1),
                value -> value.put("spurious", true));
        for (Consumer<ObjectNode> mutation : mutations) {
            ObjectNode value = fixture(); mutation.accept(value);
            assertThrows(IllegalArgumentException.class, () -> decode(value));
        }
    }
    @Test void v1NumbersRequireSafeRangeAndV2RequiresDecimalStrings() {
        ObjectNode old = legacy(fixture()); assertEquals(1, decode(old).records().size());
        row(old).put("activity_identity_u64", new BigInteger("9007199254740993"));
        assertThrows(IllegalArgumentException.class, () -> decode(old));
        ObjectNode fresh = fixture(); row(fresh).put("activity_identity_u64", 123);
        assertThrows(IllegalArgumentException.class, () -> decode(fresh));
    }
    @Test void availabilityCoverageAndActorIdentityDoNotBecomeZeroSamples() {
        ObjectNode input = fixture(); input.put("available", false).put("unavailable_reason", "observer_detached");
        assertThrows(IllegalArgumentException.class, () -> decode(input));
        input.withArray("records").removeAll(); input.put("record_count", 0);
        Journal unavailable = decode(input);
        assertTrue(unavailable.records().isEmpty()); assertFalse(unavailable.available());
        assertTrue(CompletionCallJournal.consume(unavailable, ACTIVITY).isEmpty());
        assertEquals("observer_detached", unavailable.unavailableReason().orElseThrow());
    }
    private static Journal decode(ObjectNode node) { return CompletionCallJournal.decode(StrictJson.canonical(node, CompletionCallJournal.MAX_BYTES), SOURCE); }
    private static ObjectNode row(ObjectNode input) { return (ObjectNode) input.get("records").get(0); }
    private static ObjectNode after(ObjectNode input) { return (ObjectNode) row(input).get("after"); }
    private static ObjectNode fixture() {
        ObjectNode root = StrictJson.object(); root.put("schema", CompletionCallJournal.V2).put("available", true)
                .putNull("unavailable_reason").put("observer_attached", true).put("read_only", true)
                .put("process_lifetime", true).put("query_thread_id_u32", 77).put("query_actor_full_id_u32", 40526)
                .put("record_capacity", 64).put("earliest_retained_sequence_u64", "1").put("latest_capture_sequence_u64", "1")
                .put("overflow_dropped_count_u64", "0").put("pairing_dropped_count_u64", "0").put("record_count", 1);
        ObjectNode row = root.putArray("records").addObject();
        row.put("capture_sequence_u64", "1").put("observer_invocation_sequence_u64", "1").put("capture_thread_id_u32", 77)
                .put("source_call_rva_u64", 0x23F6B82).put("source_callee_rva_u64", 0x3765760)
                .put("source_return_rva_u64", 0x23F6B87).put("source_after_cut_rva_u64", 0x23F6B87)
                .putNull("intervening_call_rva_u64").putNull("intervening_callee_rva_u64")
                .put("observation_scope", "original_completion_call").put("original_call_return_observed", true)
                .put("same_activity_full_id_observed", true).put("same_activity_full_id", true)
                .put("same_participant_full_id_observed", true).put("same_participant_full_id", true);
        for (String key : List.of("activity_identity_u64", "participant_identity_u64", "effect_identity_u64", "native_context_identity_u64", "original_parent_rsp_u64")) row.put(key, "123456");
        for (String side : List.of("before", "after")) {
            ObjectNode face = row.putObject(side); face.put("frame_observed", true);
            face.putObject("frame").put("date_raw_i64", "53200000").put("actor_character_id_i32", 40526)
                    .put("owner_thread_id_u32", 77).put("paused", false).put("map_ready", true)
                    .put("has_played_character", true).put("played_character_alive", true);
            face.put("activity_full_id_observed", true).put("activity_full_id_u32", ACTIVITY).put("activity_instance_generation_u8", 5)
                    .put("host_observed", true).put("host_character_id_i32", 40526).put("type_observed", true)
                    .put("type_identity_u64", "123456").put("type_key_observed", true).put("type_key", "activity_feast")
                    .put("participant_full_id_observed", true).put("participant_full_id_u32", 40526).put("participant_instance_generation_u8", 0)
                    .put("resource_extension_observed", true).put("resource_extension_identity_u64", "123456")
                    .put("prestige_observed", true).put("prestige_raw_i64", "100").put("stress_observed", true).put("stress_raw_i32", 100)
                    .put("reveler_xp_observed", false).putNull("reveler_xp_raw_i64").put("reveler_xp_unavailable_reason", "no_raw_only_reveler_xp_reader")
                    .put("completed_observed", true).put("completed_raw_u8", 0).put("invalidated_observed", true).put("invalidated_raw_u8", 0)
                    .put("native_completion_stamp_observed", true).put("native_completion_stamp_raw_u64", "0");
        }
        return root;
    }
    private static ObjectNode legacy(ObjectNode input) {
        input.put("schema", CompletionCallJournal.V1);
        for (String side : List.of("before", "after")) ((ObjectNode) row(input).get(side)).remove(List.of("completed_observed", "completed_raw_u8", "invalidated_observed", "invalidated_raw_u8", "native_completion_stamp_observed", "native_completion_stamp_raw_u64"));
        numbers(input); return input;
    }
    private static void numbers(JsonNode node) {
        if (node instanceof ObjectNode object) {
            var fields = object.fieldNames(); java.util.ArrayList<String> keys = new java.util.ArrayList<>(); fields.forEachRemaining(keys::add);
            for (String key : keys) {
                JsonNode value = object.get(key);
                if ((key.endsWith("_u64") || key.endsWith("_i64")) && value.isTextual()) object.put(key, new BigInteger(value.textValue()));
                else numbers(value);
            }
        } else if (node.isArray()) for (JsonNode item : node) numbers(item);
    }
}
