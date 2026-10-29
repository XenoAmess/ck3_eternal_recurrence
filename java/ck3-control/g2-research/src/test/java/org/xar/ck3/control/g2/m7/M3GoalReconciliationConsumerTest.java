package org.xar.ck3.control.g2.m7;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.governance.succession.SuccessionNativeEstate12004;

/** Actual estate/codec/goal producers. Software data grants no Root or Game custody. */
final class M3GoalReconciliationConsumerTest {
    private static final List<String> TITLE_FIELDS = List.of("expected_inherited_title_ids", "matched_inherited_title_ids",
            "missing_expected_inherited_title_ids", "unexpected_retained_predecessor_title_ids", "expected_other_heir_title_ids",
            "expected_without_heir_title_ids", "observed_additional_successor_title_ids");

    @Test void actualEstateFeedsGoalPersistenceAndNextOrdinaryPlanWithEveryTitleClass() {
        byte[] original = produced(3, false, 100, 101);
        var decoded = GoalCodec.decodeReconciliation(original);
        assertEquals(OrdinaryCampaignGoal.Verdict.MATCHED, decoded.verdict());
        assertEquals(List.of(10L, 11L), decoded.matchedInheritedTitleIds());
        assertEquals(List.of(20L), decoded.expectedOtherHeirTitleIds());
        assertEquals(List.of(30L), decoded.expectedWithoutHeirTitleIds());
        assertEquals(List.of(50), ids(object(StrictJson.parse(original)).get("observed_additional_successor_title_ids")));
        var continued = OrdinaryCampaignGoal.continueGoal(OrdinaryCampaignGoal.newGoal("m3-consumer", 2), decoded);
        var restored = GoalCodec.decodeGoal(GoalCodec.encodeGoal(continued));
        assertEquals(continued, restored);
        assertEquals(2, restored.originCharacterId()); assertEquals(3, restored.currentCharacterId());
        assertEquals(1, restored.progress().reconciledSuccessions());
        var last = restored.progress().lastSuccession().orElseThrow();
        assertEquals(decoded.matchedInheritedTitleIds(), last.matchedInheritedTitleIds());
        assertEquals(decoded.expectedOtherHeirTitleIds(), last.expectedOtherHeirTitleIds());
        assertEquals(decoded.expectedWithoutHeirTitleIds(), last.expectedWithoutHeirTitleIds());
        var next = OrdinaryCampaignGoal.plan(restored);
        assertEquals(3, next.currentCharacterId()); assertEquals(restored.progress(), next.progress());
        assertEquals(next, GoalCodec.decodePlan(GoalCodec.encodePlan(next)));
        assertTrue(next.priorities().stream().anyMatch(priority -> priority.action().equals("review_current_ruler_succession_and_partition")));
        assertArrayEquals(original, produced(3, false, 100, 101));
    }

    @Test void actualMissingRetainedAndAdditionalTitlesAndDifferentActorRemainUncredited() {
        byte[] distribution = produced(3, true, 100, 101);
        ObjectNode wire = object(StrictJson.parse(distribution));
        assertEquals(List.of(11), ids(wire.get("missing_expected_inherited_title_ids")));
        assertEquals(List.of(20, 30), ids(wire.get("unexpected_retained_predecessor_title_ids")));
        assertEquals(List.of(50), ids(wire.get("observed_additional_successor_title_ids")));
        var mismatch = GoalCodec.decodeReconciliation(distribution);
        assertEquals(OrdinaryCampaignGoal.Verdict.TITLE_DISTRIBUTION_MISMATCH, mismatch.verdict());
        assertThrows(IllegalArgumentException.class, () -> OrdinaryCampaignGoal.continueGoal(
                OrdinaryCampaignGoal.newGoal("m3-consumer", 2), mismatch));
        var changed = GoalCodec.decodeReconciliation(produced(5, false, 100, 101));
        assertEquals(OrdinaryCampaignGoal.Verdict.UNEXPECTED_SUCCESSOR, changed.verdict());
        assertThrows(IllegalArgumentException.class, () -> OrdinaryCampaignGoal.continueGoal(
                OrdinaryCampaignGoal.newGoal("m3-consumer", 2), changed));
    }

    @Test void actualNoPrimaryHeirPredictionRemainsAValidUncreditedComparison() {
        ObjectNode original = root(11, 2, false, false, 100);
        ObjectNode context = object(original.get("campaign_root_context"));
        context.putArray("primary_title_succession_character_ids");
        object(context.get("held_title_partition").get(0)).putNull("first_heir_character_id");
        var frozen = SuccessionNativeEstate12004.freeze(bytes(original), semantic(11, 2, false, 100));
        var compared = SuccessionNativeEstate12004.reconcile(frozen, bytes(root(13, 3, true, false, 101)), semantic(13, 3, true, 101));
        assertNull(frozen.expectation().expectedSuccessorCharacterId());
        var decoded = GoalCodec.decodeReconciliation(compared.wire());
        assertEquals(OrdinaryCampaignGoal.Verdict.UNEXPECTED_SUCCESSOR, decoded.verdict());
        assertEquals(List.of(), decoded.matchedInheritedTitleIds());
        assertEquals(List.of(11L, 20L), decoded.expectedOtherHeirTitleIds());
        assertEquals(List.of(10L, 30L), decoded.expectedWithoutHeirTitleIds());
        assertThrows(IllegalArgumentException.class, () -> OrdinaryCampaignGoal.continueGoal(
                OrdinaryCampaignGoal.newGoal("m3-consumer", 2), decoded));
    }

    @Test void conflictingPartitionsAndIncompleteAccountingCannotMintMatchedProgress() {
        reject(row -> row.putArray("expected_other_heir_title_ids").add(10).add(20));
        reject(row -> row.putArray("expected_without_heir_title_ids").add(10).add(30));
        reject(row -> row.putArray("expected_without_heir_title_ids").add(20).add(30));
        reject(row -> row.putArray("observed_additional_successor_title_ids").add(10).add(50));
        reject(row -> row.putArray("matched_inherited_title_ids").add(10));
        reject(row -> row.putArray("missing_expected_inherited_title_ids").add(10));
        reject(row -> row.putArray("unexpected_retained_predecessor_title_ids").add(99));
        reject(row -> row.putArray("expected_inherited_title_ids"));
        for (String field : TITLE_FIELDS) {
            reject(row -> row.putArray(field).add(10).add(10));
            reject(row -> row.putArray(field).add(20).add(10));
            reject(row -> row.remove(field));
            for (String token : List.of("true", "1.0", "\"1\"", "null", "0", "2147483648")) {
                reject(row -> row.putArray(field).add(StrictJson.parse(token.getBytes(StandardCharsets.UTF_8))));
            }
        }
    }

    @Test void verdictFlagsAndActorMustAgreeWithCompleteActualOutcomes() {
        reject(row -> row.put("successor_match", false));
        reject(row -> row.put("title_distribution_match", false));
        reject(row -> row.put("expected_successor_character_id", 4));
        reject(row -> row.putNull("expected_successor_character_id"));
        reject(row -> row.put("expected_successor_character_id", 2));
        reject(row -> row.put("actual_successor_character_id", 5));
        for (String verdict : List.of("unexpected_successor", "title_distribution_mismatch", "unknown", "unavailable")) {
            reject(row -> row.put("verdict", verdict));
        }
        ObjectNode inconsistent = object(StrictJson.parse(produced(3, true, 100, 101)));
        inconsistent.put("title_distribution_match", true);
        assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeReconciliation(bytes(inconsistent)));
    }

    @Test void signedInt32DatesSurviveButRegressionAndWrongDateTokensAreRejected() {
        assertEquals(OrdinaryCampaignGoal.Verdict.MATCHED,
                GoalCodec.decodeReconciliation(produced(3, false, Integer.MIN_VALUE, Integer.MAX_VALUE)).verdict());
        reject(row -> object(row.get("successor_binding")).put("date_raw", 99));
        for (String binding : List.of("predecessor_binding", "successor_binding")) {
            for (String token : List.of("true", "1.0", "\"100\"", "null", "-2147483649", "2147483648")) {
                reject(row -> object(row.get(binding)).set("date_raw", StrictJson.parse(token.getBytes(StandardCharsets.UTF_8))));
            }
        }
    }

    @Test void sourceRevisionsCannotRegressEvenWhenTheDisplayedDateAndOutcomeMatch() {
        for (String field : List.of("revision", "native_revision")) {
            reject(row -> object(row.get("successor_binding")).put(field, 0));
            ObjectNode same = object(StrictJson.parse(produced(3, false, 100, 101)));
            object(same.get("successor_binding")).set(field, same.get("predecessor_binding").get(field));
            assertEquals(OrdinaryCampaignGoal.Verdict.MATCHED, GoalCodec.decodeReconciliation(bytes(same)).verdict());
        }
    }

    @Test void persistedGoalAndOrdinaryPlanCannotCarryContradictoryInheritanceProgress() {
        var original = OrdinaryCampaignGoal.newGoal("m3-consumer", 2);
        var continued = OrdinaryCampaignGoal.continueGoal(original, GoalCodec.decodeReconciliation(produced(3, false, 100, 101)));
        ObjectNode good = object(StrictJson.parse(GoalCodec.encodeGoal(continued)));
        for (Consumer<ObjectNode> mutation : List.<Consumer<ObjectNode>>of(
                row -> object(row.get("progress")).put("reconciled_successions", 0),
                row -> object(row.get("progress")).putNull("last_succession"),
                row -> row.put("current_character_id", 4),
                row -> row.put("origin_character_id", 4),
                row -> last(row).put("predecessor_character_id", 3),
                row -> last(row).putArray("matched_inherited_title_ids"),
                row -> last(row).putArray("matched_inherited_title_ids").add(11).add(10),
                row -> last(row).putArray("expected_other_heir_title_ids").add(10).add(20),
                row -> last(row).putArray("expected_without_heir_title_ids").add(20).add(30))) {
            ObjectNode changed = good.deepCopy(); mutation.accept(changed);
            assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeGoal(bytes(changed)));
        }
        for (String field : List.of("matched_inherited_title_ids", "expected_other_heir_title_ids", "expected_without_heir_title_ids")) {
            ObjectNode missing = good.deepCopy(); last(missing).remove(field);
            assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeGoal(bytes(missing)));
            for (String token : List.of("true", "1.0", "\"1\"", "null", "0", "2147483648")) {
                ObjectNode changed = good.deepCopy();
                last(changed).putArray(field).add(StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
                assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeGoal(bytes(changed)));
            }
        }
        for (String token : List.of("true", "1.0", "\"1\"", "null")) {
            ObjectNode changed = good.deepCopy();
            object(changed.get("progress")).set("reconciled_successions", StrictJson.parse(token.getBytes(StandardCharsets.UTF_8)));
            assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeGoal(bytes(changed)));
        }
        ObjectNode fresh = object(StrictJson.parse(GoalCodec.encodeGoal(original)));
        fresh.put("current_character_id", 3);
        assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeGoal(bytes(fresh)));
        var invalidTyped = new OrdinaryCampaignGoal.Goal(continued.campaignId(), 2, 4, continued.progress());
        assertThrows(IllegalArgumentException.class, () -> GoalCodec.encodeGoal(invalidTyped));
        ObjectNode plan = object(StrictJson.parse(GoalCodec.encodePlan(OrdinaryCampaignGoal.plan(continued))));
        plan.put("current_character_id", 4);
        assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodePlan(bytes(plan)));
    }

    private static ObjectNode last(ObjectNode row) { return object(row.get("progress").get("last_succession")); }

    private static void reject(Consumer<ObjectNode> mutation) {
        ObjectNode changed = object(StrictJson.parse(produced(3, false, 100, 101)));
        mutation.accept(changed);
        assertThrows(IllegalArgumentException.class, () -> GoalCodec.decodeReconciliation(bytes(changed)));
    }
    private static byte[] produced(int successor, boolean mismatch, int beforeDate, int afterDate) {
        var before = SuccessionNativeEstate12004.freeze(bytes(root(11, 2, false, false, beforeDate)), semantic(11, 2, false, beforeDate));
        return SuccessionNativeEstate12004.reconcile(before, bytes(root(13, successor, true, mismatch, afterDate)),
                semantic(13, successor, true, afterDate)).wire();
    }
    private static ObjectNode root(int revision, int actor, boolean after, boolean mismatch, int date) {
        ObjectNode result = StrictJson.object().put("step", "query-campaign-root-context-v1").put("accepted", true).put("status", "available")
                .put("query_sequence", revision).put("snapshot_revision", revision).put("backend_id", "native-headless");
        ObjectNode root = result.putObject("campaign_root_context").put("schema_version", 1).put("status", "available")
                .put("snapshot_revision", revision).put("date_raw", date).put("player_character_id", actor).put("player_character_alive", true).putNull("unavailable_reason");
        root.set("primary_title", title(10)); root.putArray("primary_title_succession_character_ids").add(after ? 6 : 3);
        root.putObject("provenance").put("game_version", "1.20.0.4").put("executable_sha256", SuccessionNativeEstate12004.EXECUTABLE_SHA256)
                .put("backend_id", "ck3-1.20.0.4-native-campaign-root-context-v1").put("held_title_ids_offset", "0x1E0").put("primary_title_rva", "0x289DA10");
        ObjectNode readiness = root.putObject("readiness");
        for (String key : List.of("player_identity_ready", "primary_title_ready", "primary_title_succession_ready", "held_title_partition_ready", "same_frame_ready")) readiness.put(key, true);
        ArrayNode rows = root.putArray("held_title_partition"); rows.add(row(10, after ? 6 : 3, true));
        if (!after || !mismatch) rows.add(row(11, after ? 6 : 3, false));
        if (!after || mismatch) { rows.add(row(20, after ? 6 : 4, false)); rows.add(row(30, after ? 6 : null, false)); }
        if (after) rows.add(row(50, 6, false));
        return result;
    }
    private static ObjectNode title(int id) { return StrictJson.object().put("title_id", id).put("tier_raw", 2).put("tier_key", "county"); }
    private static ObjectNode row(int id, Integer heir, boolean primary) {
        ObjectNode row = StrictJson.object().put("primary", primary).put("capital_province_id", id + 1);
        if (heir == null) row.putNull("first_heir_character_id"); else row.put("first_heir_character_id", heir);
        row.set("title", title(id)); return row;
    }
    private static byte[] semantic(int revision, int actor, boolean changed, int date) {
        ObjectNode semantic = StrictJson.object().put("snapshot_id", "m3-goal-" + revision).put("revision", revision + 100).put("native_revision", revision)
                .put("date_raw", date).put("episode_run_id", "m3-old-episode").put("episode_character_id", 2).put("paused", true).put("map_ready", true)
                .put("one_life_terminal", changed).putNull("active_event").putNull("pending_character_interaction");
        if (changed) semantic.put("one_life_terminal_reason", "played_character_changed"); else semantic.putNull("one_life_terminal_reason");
        semantic.putObject("played_character").put("character_id", actor).put("alive", true);
        semantic.putObject("succession_lifecycle").put("lifecycle", "ordinary_campaign_succession"); return bytes(semantic);
    }
    private static List<Integer> ids(JsonNode value) {
        var result = new java.util.ArrayList<Integer>(); value.forEach(id -> result.add(id.intValue())); return List.copyOf(result);
    }
    private static ObjectNode object(JsonNode value) { return assertInstanceOf(ObjectNode.class, value); }
    private static byte[] bytes(JsonNode value) { return StrictJson.canonical(value); }
}
