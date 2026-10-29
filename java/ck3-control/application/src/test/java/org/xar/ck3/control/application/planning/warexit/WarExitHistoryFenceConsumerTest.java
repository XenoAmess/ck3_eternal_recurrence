package org.xar.ck3.control.application.planning.warexit;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.time.Instant;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningObservation;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.m0.RaiktorExitObservationCodec;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real Driver gate -> ordinary WarCore leaf; only frozen native input is synthetic. No native or Game credit. */
final class WarExitHistoryFenceConsumerTest {
    private static final Set<String> CAPS = Set.of("game.command.query-war-termination-options-N",
            "game.command.offer-white-peace-N", "game.command.surrender-war-N");
    private static final LegacyWarExitPolicy.TacticalBoundary BOUNDARY = new LegacyWarExitPolicy.TacticalBoundary(
            LegacyWarExitPolicy.Position.OBJECTIVES_EXHAUSTED_BEFORE_CAPITAL_REGROUP, 77, List.of());

    @Test void knownDeJureSubmissionDoesNotBecomeMissingImplementationAfterTheCooldown() {
        ObjectNode snapshot = snapshot(5);
        List<OpportunityJson.Obj> history = List.of(immutable(submitted("white_peace", 0)));
        var projection = WarExitCapabilities.project(immutable(snapshot), history, CAPS);
        assertEquals(WarExitCapabilities.Fence.PERMANENT_SUBMISSION, projection.gates().getFirst().whiteFence());
        assertTrue(projection.steps().isEmpty());
        assertInstanceOf(OrdinaryPolicy.Keep.class, boundary(snapshot, history, CAPS, projection.steps()));
    }

    @Test void unknownSubmissionKeepsItsActualStopReasonWithOrWithoutAnIncorrectlyRetainedLiteral() {
        ObjectNode snapshot = snapshot(5);
        ObjectNode unknown = StrictJson.object().put("command", "offer-white-peace-77"); unknown.putNull("ok");
        List<OpportunityJson.Obj> history = List.of(immutable(unknown));
        var projection = WarExitCapabilities.project(immutable(snapshot), history, CAPS);
        assertEquals(WarExitCapabilities.Fence.UNKNOWN_SUBMISSION, projection.gates().getFirst().whiteFence());
        assertTrue(projection.steps().isEmpty());
        assertUnknown(boundary(snapshot, history, CAPS, projection.steps()));
        assertUnknown(boundary(snapshot, history, CAPS, Set.of(new OperationKey("offer-white-peace-77"))));
    }

    @Test void failedOuterResultCannotDiscardTheActualQueuedTerminalReceipt() {
        ObjectNode snapshot = snapshot(5), queued = submitted("white_peace", 0); queued.put("ok", false);
        List<OpportunityJson.Obj> history = List.of(immutable(queued));
        var projection = WarExitCapabilities.project(immutable(snapshot), history, CAPS);
        assertEquals(WarExitCapabilities.Fence.UNKNOWN_SUBMISSION, projection.gates().getFirst().whiteFence());
        assertUnknown(boundary(snapshot, history, CAPS, projection.steps()));
    }

    @Test void unknownSurrenderAtTheScorePreludeAndLateBoundaryCannotBecomeUnsupportedOrReplay() {
        ObjectNode snapshot = snapshot(-100);
        ObjectNode unknown = StrictJson.object().put("command", "surrender-war-77"); unknown.putNull("ok");
        List<OpportunityJson.Obj> history = List.of(immutable(unknown));
        var projection = WarExitCapabilities.project(immutable(snapshot), history, CAPS);
        assertEquals(WarExitCapabilities.Fence.UNKNOWN_SUBMISSION, projection.gates().getFirst().surrenderFence());
        PlanningRequest request = request(snapshot, history, CAPS, projection.steps());
        assertUnknown(LegacyWarExitPolicy.evaluateScoreThresholds(request, OrdinaryPolicy.Draft.empty()));
        assertUnknown(LegacyWarExitPolicy.atBoundary(request, BOUNDARY, OrdinaryPolicy.Draft.empty()));
    }

    @Test void explicitRejectionWithoutQueuedReceiptStillAllowsOneFreshSourceBoundProposal() {
        ObjectNode snapshot = snapshot(5);
        ObjectNode failed = StrictJson.object().put("command", "offer-white-peace-77").put("ok", false);
        List<OpportunityJson.Obj> history = List.of(immutable(failed));
        var projection = WarExitCapabilities.project(immutable(snapshot), history, CAPS);
        assertEquals(WarExitCapabilities.Fence.NONE, projection.gates().getFirst().whiteFence());
        PlanningRequest request = request(snapshot, history, CAPS, projection.steps());
        var selected = assertInstanceOf(OrdinaryPolicy.Replace.class,
                LegacyWarExitPolicy.atBoundary(request, BOUNDARY, OrdinaryPolicy.Draft.empty()));
        var command = selected.draft().command().orElseThrow();
        assertEquals("offer-white-peace-77", command.operation().value());
        assertEquals(request.before(), command.before()); assertEquals(request.source(), command.source());
        assertEquals(request.sessionId(), command.sessionId()); assertEquals(request.deadline(), command.deadline());
        assertEquals(new OpportunityJson.Text("white_peace"), command.arguments().get("requested_outcome"));
        assertEquals(BigInteger.valueOf(31), command.before().frame().revision());
        assertEquals(BigInteger.valueOf(9), command.before().frame().identity().nativeRevision());
    }

    @Test void currentEpisodeAndLatestRestoreRemainTheSharedHistoryBoundary() {
        ObjectNode snapshot = snapshot(5), foreign = submitted("white_peace", 0);
        ((ObjectNode) foreign.at("/result/war_termination_result")).put("episode_run_id", "other-episode");
        assertFresh(snapshot, List.of(immutable(foreign)));
        ObjectNode restored = StrictJson.object().put("command", "restore-checkpoint").put("ok", true);
        assertFresh(snapshot, List.of(immutable(submitted("white_peace", 0)), immutable(restored)));
    }

    @Test void failedOrUnknownRestoreRowsCannotClearOriginalTerminalFences() {
        for (String status : List.of("false", "null", "missing", "1")) for (boolean wrapped : List.of(false, true)) {
            ObjectNode restore = restore(status, wrapped);
            List<OpportunityJson.Obj> known = List.of(immutable(submitted("white_peace", 0)), immutable(restore));
            ObjectNode white = snapshot(5);
            var projection = WarExitCapabilities.project(immutable(white), known, CAPS);
            assertEquals(WarExitCapabilities.Fence.PERMANENT_SUBMISSION, projection.gates().getFirst().whiteFence());
            assertTrue(projection.steps().isEmpty());
            assertInstanceOf(OrdinaryPolicy.Keep.class, boundary(white, known, CAPS, projection.steps()));
            var request = request(white, known, CAPS, projection.steps());
            assertEquals(2, WarExitEvidence.historySinceRestore(request).size());
            assertEquals(2, WarExitEvidence.effectiveHistorySinceRestore(request).size());
            assertTrue(WarExitEvidence.priorTerminalSubmission(WarExitEvidence.historySinceRestore(request), 77));

            ObjectNode unknown = StrictJson.object().put("command", "surrender-war-77"); unknown.putNull("ok");
            List<OpportunityJson.Obj> pending = List.of(immutable(unknown), immutable(restore));
            ObjectNode surrender = snapshot(-100);
            var pendingProjection = WarExitCapabilities.project(immutable(surrender), pending, CAPS);
            assertEquals(WarExitCapabilities.Fence.UNKNOWN_SUBMISSION, pendingProjection.gates().getFirst().surrenderFence());
            assertUnknown(LegacyWarExitPolicy.evaluateScoreThresholds(
                    request(surrender, pending, CAPS, pendingProjection.steps()), OrdinaryPolicy.Draft.empty()));
        }
    }

    @Test void failedRestoreKeepsOrdinaryWhitePeaceCooldownAtTheDriverConsumer() {
        ObjectNode defender = snapshot(5);
        ((ObjectNode) defender.at("/active_wars/0")).put("player_side", "defender");
        ObjectNode options = (ObjectNode) defender.at("/war_termination_options/0");
        options.put("player_side", "defender").put("attacker_war_score", -5).put("defender_war_score", 5);
        ((ObjectNode) options.at("/options/surrender")).put("outcome", "attacker_victory");
        ((ObjectNode) options.at("/options/victory")).put("outcome", "attacker_defeat");
        for (String status : List.of("false", "null", "missing", "1")) for (boolean wrapped : List.of(false, true)) {
            List<OpportunityJson.Obj> history = List.of(immutable(submitted("white_peace", 900)), immutable(restore(status, wrapped)));
            var projection = WarExitCapabilities.project(immutable(defender), history, CAPS);
            assertEquals(WarExitCapabilities.Fence.PROPOSAL_COOLDOWN, projection.gates().getFirst().whiteFence());
            assertFalse(projection.steps().contains(new OperationKey("offer-white-peace-77")));
            var request = request(defender, history, CAPS, projection.steps());
            var cooldown = WarExitEvidence.whitePeaceCooldown(WarExitEvidence.effectiveHistorySinceRestore(request), defender, 77).orElseThrow();
            assertEquals(Optional.of(100L), cooldown.elapsedRaw());
        }
    }

    @Test void onlySuccessfulRestoreClearsItsPrecedingBranchAndKeepsLaterTerminalEvidence() {
        for (boolean wrapped : List.of(false, true)) {
            ObjectNode current = snapshot(5);
            List<OpportunityJson.Obj> history = List.of(immutable(submitted("white_peace", 0)), immutable(restore("true", wrapped)));
            assertFresh(current, history);
            var request = request(current, history, CAPS, Set.of());
            assertTrue(WarExitEvidence.effectiveHistorySinceRestore(request).isEmpty());
            if (!wrapped) assertTrue(WarExitEvidence.historySinceRestore(request).isEmpty());
            ObjectNode unknown = StrictJson.object().put("command", "offer-white-peace-77"); unknown.putNull("ok");
            List<OpportunityJson.Obj> later = List.of(history.get(0), history.get(1), immutable(unknown));
            var projection = WarExitCapabilities.project(immutable(current), later, CAPS);
            assertEquals(WarExitCapabilities.Fence.UNKNOWN_SUBMISSION, projection.gates().getFirst().whiteFence());
            assertUnknown(boundary(current, later, CAPS, projection.steps()));
            assertEquals(1, WarExitEvidence.effectiveHistorySinceRestore(request(current, later, CAPS, projection.steps())).size());
        }
    }

    private static ObjectNode restore(String status, boolean wrapped) {
        ObjectNode row = StrictJson.object().put("command", wrapped ? "auto-turn" : "restore-checkpoint");
        if (!status.equals("missing")) row.set("ok", StrictJson.parse(status.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        ObjectNode result = StrictJson.object().put("step", "restore-checkpoint").put("accepted", true);
        // This is legacy history DATA, not a newly qualified restore or a native ACK-derived success.
        result.put("status", status.equals("true") ? "restored" : "submitted_pending");
        if (wrapped) row.putObject("result").putObject("auto_turn").put("selected_step", "restore-checkpoint").set("result", result);
        else row.set("result", result);
        return row;
    }

    @Test void actualAutoTurnHistoryWrapperPreservesTheDriverFenceInThePlanner() {
        ObjectNode snapshot = snapshot(5), terminal = submitted("white_peace", 0);
        ObjectNode wrapper = StrictJson.object().put("command", "auto-turn").put("ok", true);
        ObjectNode auto = wrapper.putObject("result").putObject("auto_turn").put("selected_step", "offer-white-peace-77");
        auto.set("result", terminal.get("result"));
        List<OpportunityJson.Obj> history = List.of(immutable(wrapper));
        var projection = WarExitCapabilities.project(immutable(snapshot), history, CAPS);
        assertEquals(WarExitCapabilities.Fence.PERMANENT_SUBMISSION, projection.gates().getFirst().whiteFence());
        assertInstanceOf(OrdinaryPolicy.Keep.class, boundary(snapshot, history, CAPS, projection.steps()));
    }

    @Test void aRealMissingCapabilityStillReportsUnsupportedAndBoolWarIdentityNeverClearsUnknown() {
        ObjectNode snapshot = snapshot(5);
        Set<String> missing = new HashSet<>(CAPS); missing.remove("game.command.offer-white-peace-N");
        var projection = WarExitCapabilities.project(immutable(snapshot), List.of(), missing);
        var unsupported = assertInstanceOf(OrdinaryPolicy.Stop.class, boundary(snapshot, List.of(), missing, projection.steps()));
        assertEquals(PlanningResult.StopReason.UNSUPPORTED_ACTION, unsupported.stopReason());
        ObjectNode malformed = submitted("white_peace", 0);
        ((ObjectNode) malformed.at("/result/war_termination_result")).put("war_id", true);
        List<OpportunityJson.Obj> history = List.of(immutable(malformed));
        var malformedProjection = WarExitCapabilities.project(immutable(snapshot), history, CAPS);
        assertEquals(WarExitCapabilities.Fence.UNKNOWN_SUBMISSION, malformedProjection.gates().getFirst().whiteFence());
        assertUnknown(boundary(snapshot, history, CAPS, malformedProjection.steps()));
    }

    private static OrdinaryPolicy.Decision boundary(ObjectNode snapshot, List<OpportunityJson.Obj> history,
            Set<String> caps, Set<OperationKey> steps) {
        return LegacyWarExitPolicy.atBoundary(request(snapshot, history, caps, steps), BOUNDARY, OrdinaryPolicy.Draft.empty());
    }
    private static void assertFresh(ObjectNode snapshot, List<OpportunityJson.Obj> history) {
        var projection = WarExitCapabilities.project(immutable(snapshot), history, CAPS);
        assertEquals(WarExitCapabilities.Fence.NONE, projection.gates().getFirst().whiteFence());
        assertInstanceOf(OrdinaryPolicy.Replace.class, boundary(snapshot, history, CAPS, projection.steps()));
    }
    private static void assertUnknown(OrdinaryPolicy.Decision decision) {
        var stopped = assertInstanceOf(OrdinaryPolicy.Stop.class, decision);
        assertEquals(PlanningResult.StopReason.UNKNOWN_ACTION_UNRESOLVED, stopped.stopReason());
    }
    private static PlanningRequest request(ObjectNode snapshot, List<OpportunityJson.Obj> history,
            Set<String> caps, Set<OperationKey> steps) {
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(7),
                BigInteger.valueOf(9), BigInteger.valueOf(1000)), "native:9", BigInteger.valueOf(31), "episode");
        var before = new ObservationIdentity("test-machine", new GameGeneration(44,
                new PythonOnlyUInt64(BigInteger.ONE)), frame, 1);
        Instant now = Instant.parse("2026-10-25T00:00:00Z");
        var source = new G2Source(before.machineId(), now.toString(), "fixture-build", new ExactRef("fixture", 1, "a".repeat(64)));
        var observation = new PlanningObservation(immutable(snapshot), history, steps, caps,
                Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false);
        return new PlanningRequest(before, source, "fixture-session", now.plusSeconds(60), observation);
    }
    private static ObjectNode snapshot(int score) {
        ObjectNode snapshot = StrictJson.object().put("snapshot_id", "native:9").put("revision", 31).put("native_revision", 9)
                .put("episode_run_id", "episode").put("date_raw", 1000).put("paused", true).put("map_ready", true);
        snapshot.putObject("played_character").put("character_id", 7); snapshot.putArray("player_armies");
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
                .put("terms_observable", false).put("ai_acceptance_observable", true).put("auto_accept_observable", true).put("auto_accept", true);
        option.putObject("terms").put("status", "unavailable").put("reason", "cb_specific_terms_not_observable");
        option.putObject("ai_acceptance").put("raw", 1).put("scale", 100000);
        ObjectNode response = option.putObject("recipient_response");
        if (valid) response.put("status", "available").put("decision_status_raw", 0).put("would_accept_now", true);
        else response.put("status", "unavailable").putNull("decision_status_raw").putNull("would_accept_now");
        return option;
    }
    private static ObjectNode submitted(String outcome, int date) {
        ObjectNode row = StrictJson.object().put("command", outcome.equals("white_peace") ? "offer-white-peace-77" : "surrender-war-77").put("ok", true);
        ObjectNode action = row.putObject("result").putObject("war_termination_result").put("war_id", 77)
                .put("outcome", outcome).put("episode_run_id", "episode").put("status", "submitted_pending").put("submitted_date_raw", date);
        action.putObject("casus_belli").put("database_index", 17).put("canonical_key", "individual_county_de_jure_cb");
        return row;
    }
    /** Encode and parse the actual JSON type domain, rather than passing a mutable model into a consumer. */
    private static OpportunityJson.Obj immutable(ObjectNode value) {
        return OpportunityJson.object(OpportunityJson.parse(RaiktorExitObservationCodec.encodeWire(value)), "frozen software native input");
    }
}
