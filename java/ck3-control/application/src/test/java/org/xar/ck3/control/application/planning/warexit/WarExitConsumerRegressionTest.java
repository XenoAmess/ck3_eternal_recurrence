package org.xar.ck3.control.application.planning.warexit;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.m0.RaiktorExitObservationCodec;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Software packet/real shared consumer regressions; no fixture here claims a native observation. */
final class WarExitConsumerRegressionTest {
    private static final Set<String> CAPS = Set.of("game.command.query-war-termination-options-N",
            "game.command.offer-white-peace-N", "game.command.surrender-war-N");

    @Test void unequalPublicAndNativeFrameSurvivesWireAndInboundTypedProjection() {
        ObjectNode input = snapshot(5);
        ObjectNode decoded = (ObjectNode) StrictJson.parse(RaiktorExitObservationCodec.encodeWire(input));
        var current = assertInstanceOf(WarExitInboundProvider.Current.class,
                WarExitInboundProvider.project(before(), decoded, Set.of(), 77));
        assertEquals(BigInteger.valueOf(31), current.before().frame().revision());
        assertEquals(BigInteger.valueOf(9), current.validated().binding().nativeRevision());
        assertEquals(400, current.options().durationDays().orElseThrow());
        assertEquals(WarExitEvidence.Outcome.WHITE_PEACE, current.options().whitePeace().outcome());
        input.withArray("war_termination_options").removeAll();
        assertEquals(400, current.options().durationDays().orElseThrow(), "caller mutation cannot alter typed input");
    }

    @Test void staleAndDuplicateCurrentRowsRequireAnActualNewRead() {
        ObjectNode stale = snapshot(5); options(stale).put("queried_revision", 30);
        var need = assertInstanceOf(WarExitInboundProvider.NeedRead.class,
                WarExitInboundProvider.project(before(), stale, Set.of(new OperationKey("query-war-termination-options-77")), 77));
        assertTrue(need.reachable()); assertEquals("query-war-termination-options-77", need.query().value());
        ObjectNode duplicate = snapshot(5); duplicate.withArray("war_termination_options").add(options(duplicate).deepCopy());
        assertInstanceOf(WarExitInboundProvider.NeedRead.class,
                WarExitInboundProvider.project(before(), duplicate, Set.of(), 77));
    }

    @Test void wrongTypesMissingFieldsAndUntrustedProvenanceCannotBecomeCurrentInputs() {
        for (String field : List.of("war_id", "query_sequence", "queried_native_revision")) {
            ObjectNode malformed = snapshot(5); options(malformed).put(field, true);
            assertThrows(IllegalArgumentException.class,
                    () -> WarExitInboundProvider.project(before(), malformed, Set.of(), 77));
        }
        ObjectNode missing = snapshot(5); options(missing).remove("cb_allows_white_peace");
        assertThrows(IllegalArgumentException.class, () -> WarExitInboundProvider.project(before(), missing, Set.of(), 77));
        ObjectNode foreign = snapshot(5); options(foreign).put("source", "cached_guess");
        assertThrows(IllegalArgumentException.class, () -> WarExitInboundProvider.project(before(), foreign, Set.of(), 77));
        ObjectNode crossed = snapshot(5); crossed.put("native_revision", 31);
        assertThrows(IllegalArgumentException.class, () -> WarExitInboundProvider.project(before(), crossed, Set.of(), 77));
    }

    @Test void knownUnavailableDurationAndAbsentWarRemainDistinctFromAReadyWar() {
        ObjectNode unknown = snapshot(5); options(unknown).putNull("war_duration_days");
        var current = assertInstanceOf(WarExitInboundProvider.Current.class,
                WarExitInboundProvider.project(before(), unknown, Set.of(), 77));
        assertTrue(current.options().durationDays().isEmpty());
        assertTrue(WarExitCapabilities.steps(immutable(unknown), List.of(), CAPS).isEmpty());
        ObjectNode absent = snapshot(5); absent.withArray("active_wars").removeAll();
        assertInstanceOf(WarExitInboundProvider.Unavailable.class,
                WarExitInboundProvider.project(before(), absent, Set.of(), 77));
    }

    @Test void nativePositiveQuoteCannotSubstituteForFinalAttackerAcceptance() {
        ObjectNode ready = snapshot(5);
        assertTrue(WarExitCapabilities.steps(immutable(ready), List.of(), CAPS).contains(new OperationKey("offer-white-peace-77")));
        ObjectNode unknown = snapshot(5); ObjectNode answer = (ObjectNode) options(unknown).at("/options/white_peace/recipient_response");
        answer.put("status", "unavailable").putNull("decision_status_raw").putNull("would_accept_now");
        assertTrue(WarExitCapabilities.steps(immutable(unknown), List.of(), CAPS).isEmpty());
        ObjectNode defender = snapshot(5); war(defender).put("player_side", "defender"); options(defender).put("player_side", "defender");
        options(defender).put("attacker_war_score", -5).put("defender_war_score", 5);
        ((ObjectNode) options(defender).at("/options/surrender")).put("outcome", "attacker_victory");
        ((ObjectNode) options(defender).at("/options/victory")).put("outcome", "attacker_defeat");
        ObjectNode defenderAnswer = (ObjectNode) options(defender).at("/options/white_peace/recipient_response");
        defenderAnswer.put("status", "unavailable").putNull("decision_status_raw").putNull("would_accept_now");
        assertTrue(WarExitCapabilities.steps(immutable(defender), List.of(), CAPS).contains(new OperationKey("offer-white-peace-77")),
                "the original defender proposal uses legality/positive quote without predicting acceptance");
    }

    @Test void survivingUnknownAndPermanentDeJureSubmissionsBlockFreshLiteralProjection() {
        ObjectNode snapshot = snapshot(5);
        ObjectNode unknown = StrictJson.object().put("command", "offer-white-peace-77"); unknown.putNull("ok");
        assertTrue(WarExitCapabilities.steps(immutable(snapshot), List.of(immutable(unknown)), CAPS).isEmpty());
        ObjectNode applied = submitted("white_peace", 0); // More than 30 days ago; exact de-jure fence still holds.
        assertTrue(WarExitCapabilities.steps(immutable(snapshot), List.of(immutable(applied)), CAPS).isEmpty());
        applied.put("ok", false); // Failure retains queued terminal.
        assertTrue(WarExitCapabilities.steps(immutable(snapshot), List.of(immutable(applied)), CAPS).isEmpty());
        ObjectNode defeated = snapshot(-1); ObjectNode surrender = submitted("attacker_defeat", 0);
        surrender.put("command", "surrender-war-77");
        assertTrue(WarExitCapabilities.steps(immutable(defeated), List.of(immutable(surrender)), CAPS).isEmpty());
    }

    @Test void realHistoryCooldownFeedsExactTenDayLateResponseBoundary() {
        for (int elapsed : List.of(0, 239, 240)) {
            ObjectNode snapshot = snapshot(5); snapshot.put("date_raw", elapsed);
            var pending = WarExitEvidence.whitePeaceCooldown(List.of(submitted("white_peace", 0)), snapshot, 77);
            assertEquals(elapsed < 240 ? WarExitLateBridge.ResponseWindow.ADVANCE_ONE_DAY : WarExitLateBridge.ResponseWindow.UNRESOLVED,
                    WarExitLateBridge.responseWindow(pending));
        }
        ObjectNode backwards = snapshot(5); backwards.put("date_raw", -1);
        assertEquals(WarExitLateBridge.ResponseWindow.NONE, WarExitLateBridge.responseWindow(
                WarExitEvidence.whitePeaceCooldown(List.of(submitted("white_peace", 0)), backwards, 77)));
    }

    private static ObservationIdentity before() {
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(7),
                BigInteger.valueOf(9), BigInteger.valueOf(1000)), "native:9", BigInteger.valueOf(31), "episode");
        return new ObservationIdentity("test-machine", new GameGeneration(44, new PythonOnlyUInt64(BigInteger.ONE)), frame, 1);
    }
    private static ObjectNode snapshot(int score) {
        ObjectNode snapshot = StrictJson.object().put("snapshot_id", "native:9").put("revision", 31).put("native_revision", 9)
                .put("episode_run_id", "episode").put("date_raw", 1000).put("paused", true).put("map_ready", true);
        snapshot.putObject("played_character").put("character_id", 7);
        snapshot.putObject("diagnostics").put("connection_generation", 6).put("bridge_pid", 44);
        ObjectNode war = snapshot.putArray("active_wars").addObject().put("war_id", 77).put("player_side", "attacker")
                .put("player_is_primary_war_leader", true).put("primary_opponent_character_id", 8).put("player_relative_war_score", score);
        war.putArray("targeted_title_ids").add(12);
        ObjectNode row = snapshot.putArray("war_termination_options").addObject().put("war_id", 77).put("source", "native")
                .put("player_side", "attacker").put("player_is_primary_war_leader", true).put("player_relative_war_score", score)
                .put("war_duration_days", 400).put("absolute_war_scores_observable", true).put("attacker_war_score", score)
                .put("defender_war_score", -score).put("active_casus_belli_present", true).put("cb_allows_white_peace", true)
                .put("query_sequence", 2).put("queried_snapshot_id", "native:9").put("queried_revision", 31)
                .put("queried_native_revision", 9).put("queried_connection_generation", 6).put("episode_run_id", "episode");
        row.putNull("war_score_breakdown");
        row.putObject("active_casus_belli_identity").put("database_index", 17).put("canonical_key", "individual_county_de_jure_cb");
        ObjectNode choices = row.putObject("options");
        choices.set("white_peace", option("white_peace", true)); choices.set("surrender", option("attacker_defeat", true));
        choices.set("victory", option("attacker_victory", false)); return snapshot;
    }
    private static ObjectNode option(String outcome, boolean valid) {
        ObjectNode option = StrictJson.object().put("outcome", outcome).put("hostage_variant", "none")
                .put("context_constructed", true).put("native_validator_passed", valid).put("available", valid)
                .put("terms_observable", false).put("ai_acceptance_observable", true).put("auto_accept_observable", true)
                .put("auto_accept", true);
        option.putObject("terms").put("status", "unavailable").put("reason", "cb_specific_terms_not_observable");
        option.putObject("ai_acceptance").put("raw", 1).put("scale", 100000);
        ObjectNode answer = option.putObject("recipient_response");
        if (valid) answer.put("status", "available").put("decision_status_raw", 0).put("would_accept_now", true);
        else answer.put("status", "unavailable").putNull("decision_status_raw").putNull("would_accept_now");
        return option;
    }
    private static ObjectNode submitted(String outcome, int date) {
        ObjectNode row = StrictJson.object().put("command", "offer-white-peace-77").put("ok", true);
        ObjectNode action = row.putObject("result").putObject("war_termination_result").put("war_id", 77)
                .put("outcome", outcome).put("episode_run_id", "episode").put("status", "submitted_pending").put("submitted_date_raw", date);
        action.putObject("casus_belli").put("database_index", 17).put("canonical_key", "individual_county_de_jure_cb");
        return row;
    }
    private static ObjectNode options(ObjectNode snapshot) { return (ObjectNode) snapshot.at("/war_termination_options/0"); }
    private static ObjectNode war(ObjectNode snapshot) { return (ObjectNode) snapshot.at("/active_wars/0"); }
    private static OpportunityJson.Obj immutable(ObjectNode value) {
        return OpportunityJson.object(OpportunityJson.parse(RaiktorExitObservationCodec.encodeWire(value)), "software fixture");
    }
}
