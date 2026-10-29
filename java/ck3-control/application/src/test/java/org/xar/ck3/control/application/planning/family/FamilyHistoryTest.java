package org.xar.ck3.control.application.planning.family;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.planning.family.FamilyJson.*;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

final class FamilyHistoryTest {
    private static Obj json(String text) { return decode(text.getBytes(StandardCharsets.UTF_8)); }
    private static Obj snapshot(long date) { return obj("episode_run_id", t("ep"), "date_raw", n(date),
            "played_character", json("{\"character_id\":1,\"betrothed_id\":null,\"primary_spouse_id\":null,\"spouse_ids\":[]}")); }
    private static Obj proposal() { return json("{\"command\":\"arrange-marriage-1-2\",\"ok\":true,\"result\":{\"marriage_action\":{\"status\":\"proposal_submitted\",\"played_character_id\":1,\"candidate_character_id\":2,\"submitted_date_raw\":100}}}"); }
    @Test void sevenActualSuccessfulAdvancesRecordTimeoutWithoutReplayPermission() {
        List<Obj> rows = new ArrayList<>(); rows.add(proposal());
        for (int i = 0; i < 6; i++) rows.add(json("{\"command\":\"life-advance\",\"ok\":true}"));
        assertEquals(t("pending"), FamilyHistory.rulerAttempt(rows, snapshot(124)).orElseThrow().get("status"));
        rows.add(json("{\"command\":\"life-advance\",\"ok\":true}"));
        Obj unknown = FamilyHistory.rulerAttempt(rows, snapshot(124)).orElseThrow();
        assertEquals(t("pending"), unknown.get("status"));
        assertEquals(t("proposal_timeout_unknown_no_replay"), unknown.get("reason"));
    }
    @Test void failedAdvanceIsNotProgress() {
        List<Obj> rows = new ArrayList<>(); rows.add(proposal());
        for (int i = 0; i < 8; i++) rows.add(json("{\"command\":\"life-advance\",\"ok\":false}"));
        assertEquals(t("pending"), FamilyHistory.rulerAttempt(rows, snapshot(124)).orElseThrow().get("status"));
    }
    @Test void thirtyObservedDaysDoNotEstablishNativeDisposition() {
        assertEquals(t("pending"), FamilyHistory.rulerAttempt(List.of(proposal()), snapshot(100 + 29 * 24)).orElseThrow().get("status"));
        assertEquals(t("pending"), FamilyHistory.rulerAttempt(List.of(proposal()), snapshot(100 + 30 * 24)).orElseThrow().get("status"));
        assertEquals(t("unknown_without_current_outbound_query"), FamilyHistory.rulerAttempt(List.of(proposal()), snapshot(100 + 30 * 24)).orElseThrow().get("native_pending_status"));
    }
    @Test void failedWrapperMissingActionAndHistoricalAcceptanceCannotGrantRetryOrCurrentRelationship() {
        assertEquals(t("pending"), FamilyHistory.rulerAttempt(List.of(proposal().with("ok", new Bool(false))), snapshot(124)).orElseThrow().get("status"));
        Obj absent = proposal().with("result", obj("marriage_result", json("{\"source\":\"native_relationship_snapshot\",\"candidate_character_id\":2,\"status\":\"accepted_marriage\"}")));
        assertEquals(t("pending"), FamilyHistory.rulerAttempt(List.of(absent), snapshot(124)).orElseThrow().get("status"));
        Obj action = object(object(proposal().get("result")).get("marriage_action")).with("candidate_character_id", n(3));
        assertThrows(IllegalArgumentException.class, () -> FamilyHistory.rulerAttempt(List.of(proposal().with("result", obj("marriage_action", action))), snapshot(124)));
        Obj anotherActor = proposal().with("command", t("arrange-marriage-3-2"));
        assertTrue(FamilyHistory.rulerAttempt(List.of(anotherActor), snapshot(124)).isEmpty());
    }
    @Test void currentExactNativeRelationshipCompletesWithoutAckPromotion() {
        Obj snap = snapshot(124); Obj played = object(snap.get("played_character")).with("betrothed_id", n(2));
        assertEquals(t("completed"), FamilyHistory.rulerAttempt(List.of(proposal()), snap.with("played_character", played)).orElseThrow().get("status"));
        assertEquals(t("pending"), FamilyHistory.rulerAttempt(List.of(proposal()), snap).orElseThrow().get("status"));
    }
    @Test void autoTurnPrefersFactualRootWarResult() {
        Obj row = json("{\"command\":\"auto-turn\",\"result\":{\"war_action\":{\"status\":\"actual\"},\"auto_turn\":{\"selected_step\":\"declare-war-1-2\",\"result\":{\"status\":\"plan-shaped\"}}}}");
        assertEquals("declare-war-1-2", FamilyHistory.command(row)); assertTrue(FamilyHistory.result(row).orElseThrow().get("war_action") instanceof Obj);
    }
    @Test void unknownFocusPersistsUntilExactObservedAppliedReceipt() {
        Obj pending = json("{\"command\":\"private-select-child-education-focus-v1\",\"result\":{\"action_request_id\":\"focus1\",\"status\":\"submit_unknown\",\"pre_frame\":{\"episode_run_id\":\"ep\",\"controller_full_id\":1,\"native_revision\":9}}}");
        Obj ack = json("{\"command\":\"private-query-child-education-focus-receipt-v1\",\"result\":{\"status\":\"observed_applied\",\"observed_applied\":false,\"submission\":{\"action_request_id\":\"focus1\"}}}");
        assertTrue(FamilyHistory.focusPending(List.of(pending, ack), snapshot(124)).isPresent());
        Obj applied = ack.with("result", object(ack.get("result")).with("observed_applied", new Bool(true)));
        assertTrue(FamilyHistory.focusPending(List.of(pending, applied), snapshot(124)).isEmpty());
    }
    @Test void focusAvailabilityClassesRetainSlotsWhileKnownValuesRank() {
        Obj needs = json("{\"stock_skill_options\":[{\"focus_key\":\"education_a\",\"childhood_affinity\":{\"available\":true,\"raw_value\":false},\"childhood_disaffinity\":{\"available\":false,\"raw_value\":null}},{\"focus_key\":\"education_unknown\",\"childhood_affinity\":{\"available\":false,\"raw_value\":null},\"childhood_disaffinity\":{\"available\":false,\"raw_value\":null}},{\"focus_key\":\"education_b\",\"childhood_affinity\":{\"available\":true,\"raw_value\":true},\"childhood_disaffinity\":{\"available\":false,\"raw_value\":null}}]}");
        assertEquals(List.of("education_b", "education_unknown", "education_a"), FamilyEducationPolicy.focusKeys(needs));
    }
    @Test void strictJsonRejectsDuplicateAndFloatingResourceIds() {
        assertThrows(IllegalArgumentException.class, () -> json("{\"a\":1,\"a\":2}"));
        assertThrows(IllegalArgumentException.class, () -> positive(json("{\"id\":12.0}").get("id")));
    }
}
