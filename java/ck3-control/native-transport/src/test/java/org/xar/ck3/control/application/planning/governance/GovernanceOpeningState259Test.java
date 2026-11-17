package org.xar.ck3.control.application.planning.governance;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinCodec;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy.FirstFocusDecision;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy.FocusProgress;
import org.xar.ck3.control.governance.lifestyle.LifestyleMinPolicy.ObservedTarget;
import org.xar.ck3.control.nativebridge.capabilities.governance.GovernancePlanningReads;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

import static org.junit.jupiter.api.Assertions.*;

/** Synthetic LIFE unit values; no Saved, Driver, PlanningRequest or native custody. */
final class GovernanceOpeningState259Test {
    private static final String STATE = "private-query-player-lifestyle-current-state-v1";
    private static final String WEALTH = "private-query-player-lifestyle-stock-focus-v1";
    private static final String WEALTH_KEY = "stewardship_wealth_focus";
    private static final String MARTIAL_KEY = "martial_authority_focus";
    private static final String STEWARDSHIP = "stewardship_lifestyle";
    private static final String MARTIAL = "martial_lifestyle";

    @Test
    void realProducerNegativeRetainsStateAndPositiveRetainsCompleteQuery() {
        ObjectNode state = state(true);
        ObjectNode illegal = focus(state, false);
        ObjectNode legal = focus(state, true);
        ObjectNode originalState = state.deepCopy();
        ObjectNode originalIllegal = illegal.deepCopy();
        ObjectNode originalLegal = legal.deepCopy();

        ObjectNode negative = GovernancePlanningReads.combine(state, illegal);
        assertEquals(3, negative.size());
        StrictJson.object(negative, Set.of("status", "state", "focus"));
        assertEquals("stock_focus_readback_red", negative.get("status").textValue());
        assertFalse(negative.has("step"));
        assertEquals(originalState, negative.get("state"));
        assertEquals(originalIllegal, negative.get("focus"));
        assertEquals(new OpportunityJson.Bool(false),
                OpportunityJson.object(domain(negative).get("focus"), "focus").get("native_legal"));
        assertEquals(domain(originalState), GovernanceCollector.actualLifestyleState(domain(negative)));

        ObjectNode positive = GovernancePlanningReads.combine(state, legal);
        assertEquals("stock_focus_available", positive.get("status").textValue());
        assertEquals(WEALTH, positive.get("step").textValue());
        assertEquals("stock_focus_ready", positive.get("formal_precondition_status").textValue());
        assertEquals(originalLegal, positive.get("focus_query"));
        assertEquals(originalState.get("source_frame"), positive.get("source_frame"));
        ObjectNode snapshot = (ObjectNode) positive.get("snapshot");
        ObjectNode expectedCandidates = StrictJson.object().put("status", "available").put("policy_scoped", true);
        expectedCandidates.putArray("items").addObject().put("key", WEALTH_KEY).put("lifestyle_key", STEWARDSHIP);
        assertEquals(expectedCandidates, snapshot.get("legal_focus_candidates"));
        ObjectNode expectedProgress = (ObjectNode) originalLegal.get("target_lifestyle_progress").deepCopy();
        expectedProgress.put("lifestyle_key", STEWARDSHIP);
        assertEquals(expectedProgress, snapshot.get("target_lifestyle_progress"));
        assertTrue(snapshot.get("readiness").get("legal_focus_candidates_ready").booleanValue());
        assertEquals(originalState.get("snapshot").get("current_focus"), snapshot.get("current_focus"));
        assertEquals(originalState.get("snapshot").get("current_lifestyle_progress"), snapshot.get("current_lifestyle_progress"));
        assertEquals(domain(positive), GovernanceCollector.actualLifestyleState(domain(positive)));
        assertEquals(originalState, state);
        assertEquals(originalIllegal, illegal);
        assertEquals(originalLegal, legal);
    }

    @Test
    void actualCodecAndPolicyKeepFalseObservationsAndBothFalseHasNoSelection() {
        ObjectNode input = StrictJson.object().put("schema", "lifestyle-first-focus-request-v1").put("at_peace", true);
        input.set("wealth", projection(false, WEALTH_KEY, STEWARDSHIP, progress(101, 11, 2, 3)));
        input.set("martial", projection(true, MARTIAL_KEY, MARTIAL, progress(202, 22, 4, 5)));
        input.putObject("actor_traits").put("status", "available").putArray("observed_keys");
        LifestyleMinPolicy.FirstFocusRequest first = LifestyleMinCodec.decodeFirstFocus(StrictJson.canonical(input));
        assertTrue(first.wealth().value().nativeLegal().present());
        assertEquals(Boolean.FALSE, first.wealth().value().nativeLegal().value());
        assertEquals(Boolean.TRUE, first.martial().value().nativeLegal().value());
        FocusProgress wealthProgress = new FocusProgress(BigInteger.valueOf(101), BigInteger.valueOf(11),
                BigInteger.valueOf(1000), BigInteger.valueOf(2), BigInteger.valueOf(3));
        FocusProgress martialProgress = new FocusProgress(BigInteger.valueOf(202), BigInteger.valueOf(22),
                BigInteger.valueOf(1000), BigInteger.valueOf(4), BigInteger.valueOf(5));
        assertEquals(new FirstFocusDecision(true, MARTIAL_KEY, "only_observed_final_legal_focus", 0, true,
                        new ObservedTarget(false, wealthProgress), new ObservedTarget(true, martialProgress)),
                LifestyleMinPolicy.chooseFirstFocus(first));

        ObjectNode bothFalse = input.deepCopy();
        ((ObjectNode) bothFalse.get("martial")).put("native_legal", false);
        LifestyleMinPolicy.FirstFocusRequest second = LifestyleMinCodec.decodeFirstFocus(StrictJson.canonical(bothFalse));
        assertTrue(second.martial().value().nativeLegal().present());
        assertEquals(Boolean.FALSE, second.martial().value().nativeLegal().value());
        assertEquals(new FirstFocusDecision(false, null, null, 0, true,
                        new ObservedTarget(false, wealthProgress), new ObservedTarget(false, martialProgress)),
                LifestyleMinPolicy.chooseFirstFocus(second));
    }

    @Test
    void existingFocusUsesRealNegativeWrapperAndMalformedOrCrossFrameDataRejects() {
        ObjectNode present = state(true);
        ObjectNode negative = GovernancePlanningReads.combine(present, focus(present, false));
        assertTrue(GovernancePolicies.existingFocus(domain(negative)));

        ObjectNode absent = state(false);
        ObjectNode absentNegative = GovernancePlanningReads.combine(absent, focus(absent, false));
        assertFalse(GovernancePolicies.existingFocus(domain(absentNegative)));

        ObjectNode malformed = state(true);
        ((ObjectNode) malformed.get("snapshot").get("current_lifestyle_progress")).put("xp_total_raw", -1);
        ObjectNode malformedNegative = GovernancePlanningReads.combine(malformed, focus(malformed, false));
        assertThrows(IllegalArgumentException.class, () -> GovernancePolicies.existingFocus(domain(malformedNegative)));

        ObjectNode mismatched = focus(present, false);
        ((ObjectNode) mismatched.get("source_frame")).put("native_revision", 42);
        assertThrows(IllegalArgumentException.class, () -> GovernancePlanningReads.combine(present, mismatched));
    }

    private static Obj domain(ObjectNode value) {
        return (Obj) OpportunityJson.parse(StrictJson.canonical(value));
    }

    private static ObjectNode state(boolean present) {
        ObjectNode result = StrictJson.object().put("status", "available").put("step", STATE)
                .put("formal_precondition_status", "state_only").put("episode_run_id", "unit-episode");
        result.putObject("source_frame").put("snapshot_id", "unit-public:7").put("revision", 7)
                .put("native_revision", 41).put("date_raw", 123456).put("player_character_id", 17);
        ObjectNode snapshot = result.putObject("snapshot").put("status", "available").put("snapshot_id", "unit-public:7")
                .put("episode_run_id", "unit-episode").put("public_revision", 7).put("native_revision", 41)
                .put("proof_epoch", 2).put("date_raw", 123456).put("player_character_id", 17);
        ObjectNode currentFocus = snapshot.putObject("current_focus").put("presence", present ? "present" : "absent");
        if (present) {
            currentFocus.put("key", WEALTH_KEY).put("lifestyle_key", STEWARDSHIP);
            snapshot.set("current_lifestyle_progress", progress(99, 9, 1, 2).put("lifestyle_key", STEWARDSHIP));
        } else {
            snapshot.putObject("current_lifestyle_progress").put("presence", "absent");
        }
        snapshot.putObject("target_lifestyle_progress").put("presence", "absent");
        snapshot.putArray("owned_perk_keys");
        snapshot.putObject("legal_focus_candidates").put("status", "unavailable").putArray("items");
        snapshot.putObject("legal_perk_candidates").put("status", "unavailable").putArray("items");
        snapshot.putObject("readiness").put("current_focus_ready", true).put("lifestyle_progress_ready", true)
                .put("owned_perks_ready", true).put("same_frame_ready", true)
                .put("legal_focus_candidates_ready", false).put("legal_perk_candidates_ready", false);
        return result;
    }

    private static ObjectNode focus(ObjectNode state, boolean legal) {
        ObjectNode result = StrictJson.object().put("status", "observed").put("step", WEALTH)
                .put("episode_run_id", "unit-episode").put("native_legal", legal)
                .put("target_key", WEALTH_KEY).put("target_lifestyle_key", STEWARDSHIP)
                .put("policy_scoped", true).put("read_only", true);
        result.set("source_frame", state.get("source_frame").deepCopy());
        result.set("target_lifestyle_progress", progress(101, 11, 2, 3).put("source", "exact_native_getters"));
        return result;
    }

    private static ObjectNode progress(int total, int within, int unspent, int used) {
        return StrictJson.object().put("presence", "present").put("xp_total_raw", total)
                .put("xp_within_level_raw", within).put("xp_per_level", 1000)
                .put("unspent_perk_points", unspent).put("used_perk_points", used);
    }

    private static ObjectNode projection(boolean legal, String key, String lifestyle, ObjectNode progress) {
        ObjectNode result = StrictJson.object().put("status", "observed").put("native_legal", legal)
                .put("target_key", key).put("target_lifestyle_key", lifestyle);
        result.set("target_lifestyle_progress", progress);
        return result;
    }
}
