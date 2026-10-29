package org.xar.ck3.control.application.planning;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.wave2.governance.succession.SuccessionNativeEstate12004;

/** Actual M3 and ordinary policy producers; software frames grant no Native/Root/Game authority. */
final class M3OrdinaryPlannerConsumptionTest {
    private static final Instant NOW = Instant.parse("2026-10-25T16:00:00Z");
    private static final GameGeneration GAME = new GameGeneration(123,
            new PythonOnlyUInt64(new BigInteger("134000000000000001")));

    @Test void twoRealEstateComparisonsRetainOriginAndReachTheCurrentOrdinaryPolicy() {
        var original = OrdinaryCampaignGoal.newGoal("m3-ordinary-campaign", 2);
        var first = compare(2, 3, 6, 11, 13, 100, 101, List.of(10, 11, 20, 30), List.of(10, 11, 50), true);
        var inherited = OrdinaryCampaignGoal.continueGoal(original, GoalCodec.decodeReconciliation(first));
        var restored = GoalCodec.decodeGoal(GoalCodec.encodeGoal(inherited));
        var request = request(3, 101, Optional.of(restored));
        assertEquals(Optional.of("marriage"), OrdinaryCorePolicy.focus(request));
        assertEquals(Optional.of("war"), OrdinaryCorePolicy.focus(request(3, 101, Optional.empty())),
                "the retained goal must actually change the existing ordinary focus over the old cross-run plan");
        assertEquals(List.of(20L), restored.progress().lastSuccession().orElseThrow().expectedOtherHeirTitleIds());
        assertEquals(List.of(30L), restored.progress().lastSuccession().orElseThrow().expectedWithoutHeirTitleIds());

        var second = compare(3, 6, 8, 21, 23, 101, 102, List.of(10, 11, 50), List.of(10, 11, 50, 70), false);
        var continued = OrdinaryCampaignGoal.continueGoal(restored, GoalCodec.decodeReconciliation(second));
        var secondRestore = GoalCodec.decodeGoal(GoalCodec.encodeGoal(continued));
        assertEquals(2, secondRestore.originCharacterId());
        assertEquals(6, secondRestore.currentCharacterId());
        assertEquals(2, secondRestore.progress().reconciledSuccessions());
        var last = secondRestore.progress().lastSuccession().orElseThrow();
        assertEquals(3, last.predecessorCharacterId()); assertEquals(6, last.actualSuccessorCharacterId());
        assertEquals(List.of(10L, 11L, 50L), last.matchedInheritedTitleIds());
        assertTrue(last.expectedOtherHeirTitleIds().isEmpty()); assertTrue(last.expectedWithoutHeirTitleIds().isEmpty());
        var plan = OrdinaryCampaignGoal.plan(secondRestore);
        assertEquals(plan, GoalCodec.decodePlan(GoalCodec.encodePlan(plan)));
        assertEquals(Optional.of(plan.focus()), OrdinaryCorePolicy.focus(request(6, 102, Optional.of(secondRestore))));
        assertEquals(secondRestore.progress(), plan.progress());
        assertArrayEquals(first, compare(2, 3, 6, 11, 13, 100, 101, List.of(10, 11, 20, 30), List.of(10, 11, 50), true));
    }

    @Test void theOldRulerGoalCannotEnterTheNewRulersOrdinaryRequest() {
        var old = OrdinaryCampaignGoal.newGoal("m3-ordinary-campaign", 2);
        assertThrows(IllegalArgumentException.class, () -> request(3, 101, Optional.of(old)));
    }

    private static byte[] compare(int predecessor, int successor, int nextHeir, int beforeRevision, int afterRevision,
            int beforeDate, int afterDate, List<Integer> originalTitles, List<Integer> actualTitles, boolean split) {
        var before = SuccessionNativeEstate12004.freeze(root(beforeRevision, beforeDate, predecessor, successor, originalTitles, split),
                semantic(beforeRevision, beforeDate, predecessor, predecessor, false));
        return SuccessionNativeEstate12004.reconcile(before,
                root(afterRevision, afterDate, successor, nextHeir, actualTitles, false),
                semantic(afterRevision, afterDate, predecessor, successor, true)).wire();
    }

    private static PlanningRequest request(int actor, int date, Optional<OrdinaryCampaignGoal.Goal> goal) {
        ObjectNode state = object(StrictJson.parse(semantic(31, date, actor, actor, false)));
        state.putArray("active_wars"); state.putArray("player_armies");
        var snapshot = DriverJson.object(bytes(state), DriverJson.MAX_NATIVE_BYTES);
        var identity = new ObservationIdentity("software-m3-machine", GAME,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor),
                        BigInteger.valueOf(31), BigInteger.valueOf(date)), "m3-31", BigInteger.valueOf(131), "m3-episode-" + actor), 1);
        var source = new ExactRef("software-m3-source", 1, "a".repeat(64));
        var prior = DriverJson.object("{\"priorities\":[{\"priority\":100,\"action\":\"war_expansion\",\"reason\":\"prior episode\"}]}".getBytes(java.nio.charset.StandardCharsets.UTF_8), DriverJson.MAX_NATIVE_BYTES);
        return new PlanningRequest(identity, new G2Source(identity.machineId(), NOW.toString(), "software-m3-build", source),
                "software-m3-session", NOW.plusSeconds(60), new PlanningObservation(snapshot, List.of(), Set.of(), Set.of(),
                        Optional.empty(), List.of(), goal, Optional.of(prior), false));
    }

    private static byte[] root(int revision, int date, int actor, int heir, List<Integer> titles, boolean split) {
        ObjectNode result = StrictJson.object().put("step", "query-campaign-root-context-v1").put("accepted", true).put("status", "available")
                .put("query_sequence", revision).put("snapshot_revision", revision).put("backend_id", "native-headless");
        ObjectNode root = result.putObject("campaign_root_context").put("schema_version", 1).put("status", "available")
                .put("snapshot_revision", revision).put("date_raw", date).put("player_character_id", actor).put("player_character_alive", true).putNull("unavailable_reason");
        root.set("primary_title", title(10)); root.putArray("primary_title_succession_character_ids").add(heir);
        root.putObject("provenance").put("game_version", "1.20.0.4").put("executable_sha256", SuccessionNativeEstate12004.EXECUTABLE_SHA256)
                .put("backend_id", "ck3-1.20.0.4-native-campaign-root-context-v1").put("held_title_ids_offset", "0x1E0").put("primary_title_rva", "0x289DA10");
        ObjectNode readiness = root.putObject("readiness");
        for (String field : List.of("player_identity_ready", "primary_title_ready", "primary_title_succession_ready", "held_title_partition_ready", "same_frame_ready")) readiness.put(field, true);
        var rows = root.putArray("held_title_partition");
        for (int id : titles) {
            ObjectNode row = rows.addObject().put("primary", id == 10).put("capital_province_id", id + 1);
            if (split && id == 30) row.putNull("first_heir_character_id");
            else row.put("first_heir_character_id", split && id == 20 ? 4 : heir);
            row.set("title", title(id));
        }
        return bytes(result);
    }
    private static ObjectNode title(int id) { return StrictJson.object().put("title_id", id).put("tier_raw", 2).put("tier_key", "county"); }
    private static byte[] semantic(int revision, int date, int episodeActor, int actor, boolean changed) {
        ObjectNode row = StrictJson.object().put("snapshot_id", "m3-" + revision).put("revision", revision + 100).put("native_revision", revision)
                .put("date_raw", date).put("episode_run_id", "m3-episode-" + episodeActor).put("episode_character_id", episodeActor)
                .put("paused", true).put("map_ready", true).put("one_life_terminal", changed).putNull("active_event").putNull("pending_character_interaction");
        if (changed) row.put("one_life_terminal_reason", "played_character_changed"); else row.putNull("one_life_terminal_reason");
        row.putObject("played_character").put("character_id", actor).put("alive", true);
        row.putObject("succession_lifecycle").put("lifecycle", "ordinary_campaign_succession");
        return bytes(row);
    }
    private static ObjectNode object(JsonNode value) { if(value instanceof ObjectNode object)return object;throw new IllegalArgumentException("JSON object required"); }
    private static byte[] bytes(JsonNode value) { return StrictJson.canonical(value); }
}
