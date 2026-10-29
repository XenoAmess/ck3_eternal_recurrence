package org.xar.ck3.control.application.session;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Files;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.lifecycle.NaturalSuccessionPreparation;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligation;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.events.EpisodeIncidentJournal;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisWire;
import org.xar.ck3.control.contracts.offline.RetainedIncidentBatchSource;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;

/** Real controller + real ordinary planner seams; no test runner is imported by production. */
final class SessionControllerRegressionTest {
    @TempDir Path temporary;
    private static final Instant BASE = Instant.parse("2026-10-23T15:00:00Z");
    private static final ExactRef REF = new ExactRef("D:/fixture/original.json", 1, "a".repeat(64));
    private static final GameGeneration GAME = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
    private static final SessionIdentity SESSION = new SessionIdentity("fixture-machine-1", GAME, "session-1");

    @Test void realWholePlannerPublishesSelectedReasonBeforeTheOnlyActionAndOriginalUnknownAfterward() {
        Fixture fixture = new Fixture(true);
        List<org.xar.ck3.control.application.presentation.DecisionDisplay.Snapshot> displayed = new ArrayList<>();
        var display = new org.xar.ck3.control.application.presentation.DecisionDisplay(Clock.fixed(BASE, ZoneOffset.UTC), snapshot -> {
            var card = snapshot.current().orElseThrow();
            if (card.status() == org.xar.ck3.control.application.presentation.DecisionDisplay.Status.PLANNED) {
                assertEquals(0, fixture.submitted.get());
                assertEquals(0, fixture.scopeDepth); // Whole original planning/publication scope is already closed.
                assertEquals("fixture", card.rationale());
            } else if (card.status() == org.xar.ck3.control.application.presentation.DecisionDisplay.Status.UNRESOLVED) {
                assertEquals(1, fixture.submitted.get());
            }
            displayed.add(snapshot);
        }, failure -> fail(failure.reason()));
        SessionController controller = fixture.controller(); controller.bindDecisionDisplay(display);
        BatchReport report = controller.runBatch(limits("decision-display"));
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN, report.terminal());
        assertEquals(2, displayed.size());
        var before = displayed.getFirst().current().orElseThrow();
        var after = displayed.getLast().current().orElseThrow();
        assertEquals(before.action(), after.action());
        assertEquals(report.turns().getFirst().receipt().command().origin(), after.context().origin());
        assertEquals(report.turns().getFirst().receipt().bodySha256(), after.action().orElseThrow().bodySha256());
        assertEquals(1, after.receiptSequence().orElseThrow());
        assertTrue(after.attemptRequestId().isEmpty()); // This explicit port fixture has no native attempt; never invent one.
        assertEquals(1, fixture.submitted.get());
    }

    @Test void displayFailureCannotChangeAnOriginalUnknownOrAllowAnotherSubmission() {
        Fixture fixture = new Fixture(true);
        AtomicInteger failures = new AtomicInteger();
        var display = new org.xar.ck3.control.application.presentation.DecisionDisplay(Clock.fixed(BASE, ZoneOffset.UTC),
                snapshot -> { throw new IOException("display transport unavailable"); }, failure -> failures.incrementAndGet());
        SessionController controller = fixture.controller(); controller.bindDecisionDisplay(display);
        BatchReport original = controller.runBatch(limits("display-unavailable"));
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN, original.terminal());
        assertEquals(org.xar.ck3.control.application.presentation.DecisionDisplay.Delivery.UNAVAILABLE, display.snapshot().delivery());
        assertTrue(failures.get() >= 2);
        assertEquals(original.turns().getFirst().receipt().bodySha256(),
                display.snapshot().current().orElseThrow().action().orElseThrow().bodySha256());
        controller.runBatch(limits("display-unavailable-following"));
        assertEquals(1, fixture.submitted.get());
        assertThrows(IllegalArgumentException.class, controller::resume);
        assertThrows(IllegalArgumentException.class, () -> controller.bindDecisionDisplay(display));
    }

    @Test void originalUnknownCannotBecomeACleanWorkerRestartOrClearItsQuarantine() {
        Fixture fixture=new Fixture(true);SessionController controller=fixture.controller();
        BatchReport original=controller.runBatch(limits("worker-restart-original-unknown"));
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,original.terminal());assertTrue(controller.isQuarantined());
        var before=List.copyOf(fixture.journal);var receipt=original.turns().getFirst().receipt();
        assertThrows(IllegalArgumentException.class,()->controller.drainForCleanRestart(Instant.now().plusSeconds(30)));
        assertThrows(IllegalArgumentException.class,()->controller.captureCleanRestart(null,"worker",1));
        assertThrows(IllegalArgumentException.class,()->controller.restoreCleanRestart(null,null));
        assertEquals(before,fixture.journal);assertEquals(1,fixture.submitted.get());assertTrue(controller.isQuarantined());
        assertSame(original,controller.lastReport().orElseThrow());assertSame(receipt,original.turns().getFirst().receipt());
        assertFalse(controller.isRunning());
    }
    @Test void publicPlanUsesTheExistingPlannerWithoutObservationCycleJournalOrSubmission()throws IOException {
        Fixture fixture=new Fixture(true);SessionController controller=fixture.controller();PlanningRequest original=request(BASE.plusSeconds(10));
        var selected=assertInstanceOf(PlanningResult.ActionSelected.class,controller.planPublic(original));
        assertEquals(original.before(),selected.command().before());assertEquals(original.source(),selected.command().source());
        assertEquals(0,fixture.observed.get());assertEquals(0,fixture.submitted.get());assertTrue(fixture.journal.isEmpty());
        assertTrue(controller.lastReport().isEmpty());assertFalse(controller.isRunning());assertFalse(controller.isQuarantined());
        assertDoesNotThrow(controller::requireOperatorBefore);
    }
    @Test void anUnknownOriginalStillBlocksPublicPlanningAndOperatorAcceptanceWithoutAnyNewWork() {
        Fixture fixture=new Fixture(true);SessionController controller=fixture.controller();
        BatchReport original=controller.runBatch(limits("operator-must-not-clear-unknown"));
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,original.terminal());assertTrue(controller.isQuarantined());
        int writes=fixture.journal.size(),observations=fixture.observed.get(),submits=fixture.submitted.get();
        assertThrows(IllegalArgumentException.class,()->controller.planPublic(request(BASE.plusSeconds(10))));
        assertThrows(IOException.class,controller::requireOperatorBefore);
        var data=OperatorRebindConsumerTest.data();
        assertThrows(IllegalArgumentException.class,()->controller.acceptOperatorRebound(data.actual(),BASE.plusSeconds(10)));
        assertTrue(controller.isQuarantined());assertSame(original,controller.lastReport().orElseThrow());
        assertEquals(writes,fixture.journal.size());assertEquals(observations,fixture.observed.get());assertEquals(submits,fixture.submitted.get());
    }
    @Test void evenACompleteOperatorCarrierCannotBypassTheInstalledObservationSourcesDefaultDenial() {
        Fixture fixture=new Fixture(true);SessionController controller=fixture.controller();var data=OperatorRebindConsumerTest.data();
        assertThrows(IOException.class,()->controller.acceptOperatorRebound(data.actual(),BASE.plusSeconds(10)));
        assertFalse(controller.isQuarantined());assertFalse(controller.isRunning());assertTrue(controller.lastReport().isEmpty());
        assertTrue(fixture.journal.isEmpty());assertEquals(0,fixture.submitted.get());assertEquals(0,fixture.observed.get());
    }
    @Test void strictBatchWireRejectsWrongFieldsMissingBooleanFloatAndDuplicate() {
        BatchLimits original = limits("wire"); byte[] valid = BatchLimitsWire.encode(original);
        assertEquals(original, BatchLimitsWire.decode(valid));
        String json = new String(valid, StandardCharsets.UTF_8);
        for (String invalid : List.of(json.replace("\"maximum_turns\":2", "\"maximum_turns\":true"),
                json.replace("\"maximum_turns\":2", "\"maximum_turns\":2.0"),
                json.replace("\"batch_id\":\"wire\",", ""),
                json.replace("\"batch_id\"", "\"wrong_batch_id\""),
                json.replace("\"maximum_turns\":2", "\"maximum_turns\":2,\"maximum_turns\":2")))
            assertThrows(IllegalArgumentException.class, () -> BatchLimitsWire.decode(invalid.getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> BatchLimitsWire.decode(new byte[BatchLimitsWire.MAXIMUM_BYTES + 1]));
    }
    @Test void actualInnerNonzeroExitStopsBeforeObservationActionAndSave() {
        Fixture fixture = new Fixture(false);
        fixture.life = (expected, until) -> new GameLifecycle.Exited(GAME, 19, false, GameLifecycle.TerminalKind.NATURAL_EXIT, REF);
        BatchReport report = fixture.controller().runBatch(limits("exit"));
        assertEquals(BatchReport.Terminal.INNER_EXIT, report.terminal()); assertTrue(report.detail().contains("exit=19"));
        assertEquals(0, fixture.observed.get()); assertEquals(0, fixture.submitted.get()); assertEquals(0, report.committedSavedDays());
        assertTrue(report.fullWallNanos() > 0); assertEquals(JournalKind.BATCH_INTERRUPTED, fixture.journal.getLast().kind());
    }
    @Test void readinessTimeoutRetainsZeroCreditAndCompleteFailedWallTime() {
        Fixture fixture = new Fixture(false);
        fixture.observer = (expected, until) -> { fixture.observed.incrementAndGet(); return new Waiting("map not yet ready", REF); };
        BatchReport report = fixture.controller().runBatch(new BatchLimits("readiness", 2, Duration.ofSeconds(5), Duration.ofMillis(20), Duration.ofMillis(5), 3));
        assertEquals(BatchReport.Terminal.READINESS_TIMEOUT, report.terminal()); assertTrue(fixture.observed.get() > 0);
        assertEquals(0, fixture.submitted.get()); assertEquals(0, report.committedSavedDays());
        assertTrue(report.phases().stream().anyMatch(span -> span.phase() == BatchReport.Phase.IDLE_WAIT));
    }
    @Test void missingFullProductionStageIsTerminalAndDoesNotPollOrSubmit() {
        Fixture fixture = new Fixture(false); BatchReport report = fixture.controller().runBatch(limits("missing"));
        assertEquals(BatchReport.Terminal.INCOMPLETE_MIGRATION, report.terminal());
        assertEquals(1, fixture.observed.get()); assertEquals(0, fixture.submitted.get()); assertEquals(0, report.committedSavedDays());
    }
    @Test void noInitialSavedPairStillEntersOrdinaryPlannerWithoutCheckpointSubmission() {
        Fixture fixture=new Fixture(true);fixture.withBaseline=false;
        BatchReport report=fixture.controller().runBatch(limits("ordinary-without-initial-save"));
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,report.terminal());
        assertEquals(1,fixture.submitted.get());assertTrue(fixture.planningPublications>0);
        assertTrue(report.lastSavedPair().isEmpty());assertEquals(0,report.committedSavedDays());
        assertTrue(fixture.journal.stream().noneMatch(row->row.kind()==JournalKind.SAVE_CONFIRMED));
    }
    @Test void missingInitialPairedSaveProofStopsBeforeAnyOrdinaryGameplay() {
        Fixture fixture = new Fixture(true); fixture.withBaseline = false; fixture.cycleAvailable = false;
        BatchReport report = fixture.controller().runBatch(limits("initial-save"));
        assertEquals(BatchReport.Terminal.INCOMPLETE_MIGRATION, report.terminal());
        assertTrue(report.detail().contains("completed-cycle")); assertEquals(0, fixture.submitted.get()); assertTrue(report.lastSavedPair().isEmpty());
    }
    @Test void unknownActionIsNeverReplayedOrFollowedBySaveAcrossBatches() {
        Fixture fixture = new Fixture(true); SessionController controller = fixture.controller();
        BatchReport first = controller.runBatch(limits("unknown"));
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN, first.terminal()); assertEquals(1, fixture.submitted.get());
        assertEquals(ActionReceipt.Outcome.UNRESOLVED, first.turns().getFirst().receipt().outcome());
        assertEquals(0, first.committedSavedDays()); assertEquals("save-initial", first.lastSavedPair().orElseThrow().saveActionId());
        assertEquals(0,fixture.episodeCalls);
        int journalCalls = fixture.journal.size(); BatchReport second = controller.runBatch(limits("after-unknown"));
        assertEquals(BatchReport.Terminal.INTERNAL_FAILURE, second.terminal()); assertEquals(1, fixture.submitted.get());
        assertEquals(journalCalls, fixture.journal.size()); assertThrows(IllegalArgumentException.class, controller::resume);
        assertEquals(0,fixture.episodeCalls);
    }
    @Test void existingPendingActionUsesReadOnlyReconciliationAndRetainsItsOriginalBody() {
        Fixture fixture = new Fixture(true); fixture.reconcileExisting = true;
        BatchReport report = fixture.controller().runBatch(limits("reconcile"));
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN, report.terminal()); assertEquals(0, fixture.submitted.get()); assertEquals(1, fixture.reconciled.get());
        assertTrue(report.turns().isEmpty()); assertEquals(1, report.reconciliations().size());
        var original = report.reconciliations().getFirst().originalReceipt();
        assertEquals("original-action", original.command().actionId()); assertEquals(BASE.plusSeconds(1), original.command().deadline());
        assertEquals(0, report.committedSavedDays());
    }
    @Test void sameFinishedBatchRequestReturnsItsOriginalReportWithoutRepeatingWork() {
        Fixture fixture = new Fixture(false); SessionController controller = fixture.controller(); BatchLimits request = limits("same-batch");
        BatchReport first = controller.runBatch(request); int journals = fixture.journal.size();
        assertSame(first, controller.runBatch(request)); assertEquals(1, fixture.observed.get()); assertEquals(journals, fixture.journal.size());
        assertThrows(IllegalArgumentException.class, () -> controller.runBatch(new BatchLimits("same-batch", 1, request.wallTime(), request.readinessTimeout(), request.pollInterval(), 3)));
        assertFalse(controller.isQuarantined());
    }
    @Test void stopRequestedIsConsumedBeforeAnyGameplayAndSameControllerCanResume() {
        Fixture fixture = new Fixture(false); SessionController controller = fixture.controller(); controller.requestStop();
        assertEquals(BatchReport.Terminal.OPERATOR_STOP, controller.runBatch(limits("stop")).terminal());
        assertEquals(0, fixture.observed.get()); assertEquals(0, fixture.submitted.get());
        controller.resume(); assertEquals(BatchReport.Terminal.INCOMPLETE_MIGRATION, controller.runBatch(limits("resume")).terminal());
        assertEquals(1, fixture.observed.get()); assertEquals(SESSION, controller.identity());
    }
    @Test void writerUnknownIsNotRetriedByFinalizationAndPreventsGameCalls() {
        Fixture fixture = new Fixture(false); AtomicInteger writes = new AtomicInteger();
        fixture.writer = input -> { writes.incrementAndGet(); throw new IOException("lost actual writer completion"); };
        BatchReport report = fixture.controller().runBatch(limits("writer"));
        assertEquals(BatchReport.Terminal.WRITER_UNKNOWN, report.terminal()); assertEquals(1, writes.get());
        assertEquals(0, fixture.observed.get()); assertEquals(0, fixture.submitted.get()); assertEquals(0, report.committedSavedDays());
    }
    @Test void analysisFailurePreservesOriginalInnerExit() {
        Fixture fixture = capturedAnalysisBeforeReplan();
        var exited = new GameLifecycle.Exited(GAME, 19, false, GameLifecycle.TerminalKind.NATURAL_EXIT, REF);
        AtomicInteger checks = new AtomicInteger();
        fixture.life = (expected, until) -> checks.incrementAndGet() == 1 ? new GameLifecycle.Running(GAME, REF) : exited;
        BatchReport report = fixture.controller().runBatch(limits("analysis-after-exit"));
        assertEquals(BatchReport.Terminal.INNER_EXIT, report.terminal());
        assertSame(exited, report.lastLifecycle().orElseThrow());
        assertTrue(report.detail().contains("exit=19, timed_out=false, terminal=NATURAL_EXIT"));
        assertEquals(1, fixture.observed.get()); assertEquals(0, fixture.submitted.get());
        assertAnalysisEnqueueFailure(report);
        assertEquals(JournalKind.BATCH_INTERRUPTED, fixture.journal.getLast().kind());
    }
    @Test void analysisFailurePreservesReadinessTimeout() {
        Fixture fixture = capturedAnalysisBeforeReplan();
        BatchReport report = fixture.controller().runBatch(new BatchLimits("analysis-after-readiness", 2,
                Duration.ofSeconds(5), Duration.ofMillis(20), Duration.ofMillis(5), 3));
        assertEquals(BatchReport.Terminal.READINESS_TIMEOUT, report.terminal());
        assertTrue(report.detail().startsWith("captured incident followed by waiting"));
        assertTrue(fixture.observed.get() > 1); assertEquals(0, fixture.submitted.get());
        assertAnalysisEnqueueFailure(report);
        assertEquals(JournalKind.BATCH_DEFERRED, fixture.journal.getLast().kind());
    }
    @Test void analysisFailurePreservesWallTimeout() {
        Fixture fixture = capturedAnalysisBeforeReplan();
        BatchReport report = fixture.controller().runBatch(new BatchLimits("analysis-after-wall", 2,
                Duration.ofMillis(150), Duration.ofSeconds(1), Duration.ofMillis(5), 3));
        assertEquals(BatchReport.Terminal.WALL_TIMEOUT, report.terminal());
        assertTrue(report.detail().startsWith("complete batch monotonic wall bound expired"));
        assertTrue(fixture.observed.get() > 1); assertEquals(0, fixture.submitted.get());
        assertAnalysisEnqueueFailure(report);
        assertEquals(JournalKind.BATCH_DEFERRED, fixture.journal.getLast().kind());
    }
    @Test void analysisFailurePreservesMissingFullPlanner() {
        Fixture fixture = capturedAnalysisBeforeReplan(); fixture.publishFirstPlan = false;
        BatchReport report = fixture.controller().runBatch(limits("analysis-after-missing-stage"));
        assertEquals(BatchReport.Terminal.INCOMPLETE_MIGRATION, report.terminal());
        assertTrue(report.detail().startsWith("missing real production stages:"));
        assertEquals(1, fixture.observed.get()); assertEquals(0, fixture.submitted.get());
        assertAnalysisEnqueueFailure(report);
        assertEquals(JournalKind.BATCH_INTERRUPTED, fixture.journal.getLast().kind());
    }
    @Test void analysisFailureMakesNormalStopUnavailable() {
        Fixture fixture = new Fixture(true);
        fixture.analysis = work -> { throw new IOException("offline index unavailable"); };
        SessionController controller = fixture.controller();
        var captured = new org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest("incident-stop", REF, List.of());
        fixture.observer = (expected, until) -> {
            fixture.observed.incrementAndGet(); controller.requestStop();
            return new Ready(request(until), CheckpointEligibility.SAFE, Optional.of(captured), Optional.of(semantic(request(until))));
        };
        BatchReport report = controller.runBatch(limits("analysis-after-stop"));
        assertEquals(BatchReport.Terminal.ANALYSIS_UNAVAILABLE, report.terminal());
        assertEquals(1, fixture.observed.get()); assertEquals(0, fixture.submitted.get());
        assertAnalysisEnqueueFailure(report); assertFalse(controller.isQuarantined());
        assertEquals(JournalKind.BATCH_INTERRUPTED, fixture.journal.getLast().kind());
    }
    private static Fixture capturedAnalysisBeforeReplan() {
        Fixture fixture = new Fixture(false); fixture.publishFirstPlan = true;
        var captured = new org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest("incident-first", REF, List.of());
        fixture.observer = (expected, until) -> {
            if (fixture.observed.incrementAndGet() == 1)
                return new Ready(request(until), CheckpointEligibility.SAFE, Optional.of(captured), Optional.empty());
            return new Waiting("captured incident followed by waiting", REF);
        };
        fixture.analysis = work -> { throw new IOException("offline index unavailable"); };
        return fixture;
    }
    private static void assertAnalysisEnqueueFailure(BatchReport report) {
        assertTrue(report.detail().contains("; offline analysis enqueue failed: java.io.IOException: offline index unavailable"));
        assertEquals(1L, report.phases().stream().filter(span -> span.phase() == BatchReport.Phase.ANALYSIS_ENQUEUE
                && span.terminal() == BatchReport.PhaseTerminal.FAILED).count());
        assertEquals(0, report.committedSavedDays()); assertFalse(report.dirtySinceSave());
        assertTrue(report.turns().isEmpty()); assertTrue(report.reconciliations().isEmpty());
        assertEquals("save-initial", report.lastSavedPair().orElseThrow().saveActionId());
        assertTrue(report.fullWallNanos() > 0);
    }
    @Test void offlineAnalysisRunsAfterBatchWithoutBlockingNextBatchOrRestartingSession() {
        Fixture fixture = new Fixture(false); CompletableFuture<AnalysisCompletion> pending = new CompletableFuture<>();
        var captured = new org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest("incident-1", REF, List.of());
        fixture.observer = (expected, until) -> { fixture.observed.incrementAndGet(); return new Ready(request(until), CheckpointEligibility.SAFE, Optional.of(captured), Optional.empty()); };
        fixture.analysis = work -> new AnalysisTicket(work.batchId(), pending);
        SessionController controller = fixture.controller(); BatchReport first = controller.runBatch(limits("batch-one"));
        assertEquals(List.of("incident-1"), first.pendingAnalysisBatchIds()); assertFalse(pending.isDone());
        BatchReport second = controller.runBatch(limits("batch-two"));
        assertEquals(List.of("incident-1"), second.pendingAnalysisBatchIds()); assertEquals(2, fixture.observed.get());
        pending.complete(new AnalysisCompletion("incident-1", List.of(REF), REF));
        BatchReport third = controller.runBatch(limits("batch-three"));
        assertTrue(third.pendingAnalysisBatchIds().isEmpty()); assertEquals("incident-1", third.completedAnalyses().getFirst().batchId());
        assertEquals(0, fixture.submitted.get()); assertEquals(SESSION, third.session());
    }
    @Test void rejectedAnalysisEnqueueRetainsOriginalForTheNextBatchWithoutAnotherReady() {
        Fixture fixture = new Fixture(false);
        var original = new org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest("incident-not-accepted", REF, List.of());
        var pending = new CompletableFuture<AnalysisCompletion>(); var attempts = new AtomicInteger();
        fixture.observer = (expected, until) -> {
            fixture.observed.incrementAndGet();
            return new Ready(request(until), CheckpointEligibility.SAFE, Optional.of(original), Optional.empty());
        };
        fixture.analysis = work -> {
            assertSame(original, work, "retry must retain the captured original, without constructing another request");
            if (attempts.incrementAndGet() == 1) throw new IOException("offline index unavailable");
            return new AnalysisTicket(work.batchId(), pending);
        };
        SessionController controller = fixture.controller();
        BatchReport first = controller.runBatch(limits("analysis-not-accepted"));
        assertEquals(BatchReport.Terminal.INCOMPLETE_MIGRATION, first.terminal());
        assertAnalysisEnqueueFailure(first); assertTrue(first.pendingAnalysisBatchIds().isEmpty());
        fixture.observer = (expected, until) -> { fixture.observed.incrementAndGet(); return new Waiting("no subsequent Ready", REF); };
        BatchReport second = controller.runBatch(new BatchLimits("analysis-retry-without-ready", 1,
                Duration.ofSeconds(5), Duration.ofMillis(20), Duration.ofMillis(5), 3));
        assertEquals(BatchReport.Terminal.READINESS_TIMEOUT, second.terminal());
        assertEquals(2, attempts.get()); assertEquals(List.of(original.batchId()), second.pendingAnalysisBatchIds());
        assertEquals(1L, second.phases().stream().filter(span -> span.phase() == BatchReport.Phase.ANALYSIS_ENQUEUE
                && span.terminal() == BatchReport.PhaseTerminal.RETURNED).count());
        assertFalse(pending.isDone()); assertTrue(second.completedAnalyses().isEmpty());
        BatchReport third = controller.runBatch(new BatchLimits("analysis-already-accepted", 1,
                Duration.ofSeconds(5), Duration.ofMillis(20), Duration.ofMillis(5), 3));
        assertEquals(BatchReport.Terminal.READINESS_TIMEOUT, third.terminal()); assertEquals(2, attempts.get());
        assertEquals(List.of(original.batchId()), third.pendingAnalysisBatchIds());
        assertEquals(0, fixture.submitted.get()); assertEquals(0, third.committedSavedDays());
        assertTrue(third.turns().isEmpty()); assertFalse(controller.isQuarantined());
    }
    @Test void lateObservationRetainsActualJournalBatchButCannotEnterPlanningActionOrSave() throws IOException {
        Fixture fixture = new Fixture(true); var produced = new AtomicReference<CapturedOffline>();
        var pending = new CompletableFuture<AnalysisCompletion>(); var enqueues = new AtomicInteger();
        fixture.observer = (expected, until) -> {
            CapturedOffline actual = capturedOffline("late-journal-original", until); produced.set(actual);
            fixture.observed.incrementAndGet(); fixture.time.waitFor(Duration.ofSeconds(6));
            return new Ready(actual.request(), CheckpointEligibility.SAFE, Optional.of(actual.batch()), Optional.empty());
        };
        fixture.analysis = work -> {
            CapturedOffline actual = produced.get(); assertNotNull(actual); assertSame(actual.batch(), work);
            assertEquals(work, OfflineEventAnalysisWire.decodeBatch(OfflineEventAnalysisWire.encode(work)));
            assertEquals(work.manifestRef(), EpisodeIncidentJournal.measure(Path.of(work.manifestRef().path())));
            for (ExactRef original : work.capturedRefs()) assertEquals(original, EpisodeIncidentJournal.measure(Path.of(original.path())));
            enqueues.incrementAndGet(); return new AnalysisTicket(work.batchId(), pending);
        };
        SessionController controller = fixture.controller(); BatchReport report = controller.runBatch(limits("late-journal-batch"));
        assertEquals(BatchReport.Terminal.WALL_TIMEOUT, report.terminal()); assertEquals(1, enqueues.get());
        assertEquals(List.of(produced.get().batch().batchId()), report.pendingAnalysisBatchIds()); assertFalse(pending.isDone());
        assertEquals(0, fixture.planningPublications); assertEquals(0, fixture.submitted.get()); assertTrue(report.lastPlan().isEmpty());
        assertTrue(report.turns().isEmpty()); assertTrue(report.completedAnalyses().isEmpty()); assertEquals(0, report.committedSavedDays());
        assertFalse(report.dirtySinceSave()); assertFalse(controller.isQuarantined());
        assertTrue(report.phases().stream().noneMatch(span -> Set.of(BatchReport.Phase.PLANNING, BatchReport.Phase.ACTION,
                BatchReport.Phase.CHECKPOINT).contains(span.phase())));
        assertEquals(JournalKind.BATCH_DEFERRED, fixture.journal.getLast().kind());
        CapturedOffline actual = produced.get();
        var reopened = EpisodeIncidentJournal.openOriginal(actual.configuration(), actual.journal().episodeReference());
        assertEquals(actual.batch(), reopened.scan(new EpisodeIncidentJournal.Binding(actual.request().before(),
                actual.request().source(), actual.request().sessionId())).batch().orElseThrow(), "queue admission cannot acknowledge or invent completed research");
    }
    @Test void lateActualJournalBatchSurvivesEnqueueFailureAndNextBatchWithoutReady() throws IOException {
        Fixture fixture = new Fixture(true); var produced = new AtomicReference<CapturedOffline>();
        var pending = new CompletableFuture<AnalysisCompletion>(); var enqueues = new AtomicInteger();
        fixture.observer = (expected, until) -> {
            CapturedOffline actual = capturedOffline("late-rejected-original", until); produced.set(actual);
            fixture.time.waitFor(Duration.ofSeconds(6));
            return new Ready(actual.request(), CheckpointEligibility.SAFE, Optional.of(actual.batch()), Optional.empty());
        };
        fixture.analysis = work -> {
            assertSame(produced.get().batch(), work);
            if (enqueues.incrementAndGet() == 1) throw new IOException("offline index unavailable");
            return new AnalysisTicket(work.batchId(), pending);
        };
        SessionController controller = fixture.controller(); BatchReport first = controller.runBatch(limits("late-analysis-rejected"));
        assertEquals(BatchReport.Terminal.WALL_TIMEOUT, first.terminal()); assertAnalysisEnqueueFailure(first);
        fixture.observer = (expected, until) -> new Waiting("original late capture retained without another Ready", REF);
        BatchReport second = controller.runBatch(new BatchLimits("late-analysis-retry", 1,
                Duration.ofSeconds(5), Duration.ofMillis(20), Duration.ofMillis(5), 3));
        assertEquals(BatchReport.Terminal.READINESS_TIMEOUT, second.terminal()); assertEquals(2, enqueues.get());
        assertEquals(List.of(produced.get().batch().batchId()), second.pendingAnalysisBatchIds()); assertFalse(pending.isDone());
        assertTrue(second.completedAnalyses().isEmpty()); assertEquals(0, fixture.submitted.get()); assertEquals(0, fixture.planningPublications);
        assertEquals(0, second.committedSavedDays()); assertFalse(controller.isQuarantined());
    }
    @Test void lateObservationCannotEnqueueActualJournalDataUnderAnExtendedDeadline() throws IOException {
        Fixture fixture = new Fixture(true);
        fixture.observer = (expected, until) -> {
            CapturedOffline actual = capturedOffline("late-extended-deadline", until); fixture.time.waitFor(Duration.ofSeconds(6));
            var extended = new PlanningRequest(actual.request().before(), actual.request().source(), actual.request().sessionId(),
                    until.plusNanos(1), actual.request().observations());
            return new Ready(extended, CheckpointEligibility.SAFE, Optional.of(actual.batch()), Optional.empty());
        };
        BatchReport report = fixture.controller().runBatch(limits("late-extended-deadline"));
        assertEquals(BatchReport.Terminal.INTERNAL_FAILURE, report.terminal()); assertTrue(report.detail().contains("observation extended caller deadline"));
        assertTrue(report.pendingAnalysisBatchIds().isEmpty()); assertTrue(report.completedAnalyses().isEmpty());
        assertEquals(0, fixture.submitted.get()); assertEquals(0, fixture.planningPublications); assertEquals(0, report.committedSavedDays());
    }
    @Test void lateObservationCannotEnqueueActualJournalDataFromAnotherOwnedSession() throws IOException {
        Fixture fixture = new Fixture(true);
        fixture.observer = (expected, until) -> {
            CapturedOffline actual = capturedOffline("late-foreign-session", until); fixture.time.waitFor(Duration.ofSeconds(6));
            var foreign = new PlanningRequest(actual.request().before(), actual.request().source(), "another-session",
                    until, actual.request().observations());
            return new Ready(foreign, CheckpointEligibility.SAFE, Optional.of(actual.batch()), Optional.empty());
        };
        BatchReport report = fixture.controller().runBatch(limits("late-foreign-session"));
        assertEquals(BatchReport.Terminal.INTERNAL_FAILURE, report.terminal()); assertTrue(report.detail().contains("ordinary observation crossed owned Game/session"));
        assertTrue(report.pendingAnalysisBatchIds().isEmpty()); assertTrue(report.completedAnalyses().isEmpty());
        assertEquals(0, fixture.submitted.get()); assertEquals(0, fixture.planningPublications); assertEquals(0, report.committedSavedDays());
    }
    private record CapturedOffline(PlanningRequest request, EpisodeIncidentJournal journal,
            EpisodeIncidentJournal.Configuration configuration, BatchRequest batch) { }
    @Test void retainedJournalBatchIsScannedAndQueuedAfterInnerExitWithoutReadyOrAnotherGameRead() throws IOException {
        Fixture fixture = new Fixture(false); CapturedOffline original = capturedOffline("no-ready-inner-exit", BASE.plusSeconds(30));
        var scans = new AtomicInteger(); var enqueues = new AtomicInteger(); var pending = new CompletableFuture<AnalysisCompletion>();
        fixture.retainedSource = () -> {
            scans.incrementAndGet();
            return List.of(original.journal().scan(new EpisodeIncidentJournal.Binding(original.request().before(),
                    original.request().source(), original.request().sessionId())).batch().orElseThrow());
        };
        var exited = new GameLifecycle.Exited(GAME, 19, true, GameLifecycle.TerminalKind.DEADLINE, REF);
        fixture.life = (owner, until) -> exited;
        fixture.analysis = work -> {
            assertEquals(original.batch(), work);
            assertEquals(work, OfflineEventAnalysisWire.decodeBatch(OfflineEventAnalysisWire.encode(work)));
            assertEquals(work.manifestRef(), EpisodeIncidentJournal.measure(Path.of(work.manifestRef().path())));
            enqueues.incrementAndGet(); return new AnalysisTicket(work.batchId(), pending);
        };
        SessionController controller = fixture.controller(); BatchReport first = controller.runBatch(limits("no-ready-exited-batch"));
        assertEquals(BatchReport.Terminal.INNER_EXIT, first.terminal()); assertTrue(first.detail().contains("exit=19, timed_out=true, terminal=DEADLINE"));
        assertSame(exited, first.lastLifecycle().orElseThrow());
        assertEquals(1, scans.get()); assertEquals(1, enqueues.get()); assertEquals(0, fixture.observed.get()); assertEquals(0, fixture.submitted.get());
        assertEquals(List.of(original.batch().batchId()), first.pendingAnalysisBatchIds()); assertFalse(pending.isDone());
        assertTrue(first.completedAnalyses().isEmpty()); assertEquals(0, first.committedSavedDays());
        assertEquals(JournalKind.BATCH_INTERRUPTED, fixture.journal.getLast().kind());
        BatchReport second = controller.runBatch(limits("no-ready-exited-again"));
        assertEquals(BatchReport.Terminal.INNER_EXIT, second.terminal()); assertEquals(2, scans.get()); assertEquals(1, enqueues.get());
        assertSame(exited, second.lastLifecycle().orElseThrow());
        assertEquals(List.of(original.batch().batchId()), second.pendingAnalysisBatchIds()); assertEquals(0, fixture.observed.get());
        assertEquals(original.batch(), original.journal().scan(new EpisodeIncidentJournal.Binding(original.request().before(),
                original.request().source(), original.request().sessionId())).batch().orElseThrow());
    }
    @Test void failedNoReadyScanStillRetriesThePreviouslyUnacceptedOriginalWithoutChangingItsTerminal() throws IOException {
        Fixture fixture = new Fixture(false); CapturedOffline original = capturedOffline("no-ready-retained-retry", BASE.plusSeconds(30));
        var scans = new AtomicInteger(); var enqueues = new AtomicInteger(); var pending = new CompletableFuture<AnalysisCompletion>();
        fixture.retainedSource = () -> {
            if (scans.incrementAndGet() == 1) return List.of(original.batch());
            throw new IOException("retained source custody unavailable");
        };
        fixture.observer = (owner, until) -> { fixture.observed.incrementAndGet(); return new Waiting("no Ready for original episode", REF); };
        fixture.analysis = work -> {
            assertSame(original.batch(), work);
            if (enqueues.incrementAndGet() == 1) throw new IOException("offline index unavailable");
            return new AnalysisTicket(work.batchId(), pending);
        };
        SessionController controller = fixture.controller();
        BatchReport first = controller.runBatch(new BatchLimits("no-ready-enqueue-rejected", 1,
                Duration.ofSeconds(5), Duration.ofMillis(20), Duration.ofMillis(5), 3));
        assertEquals(BatchReport.Terminal.READINESS_TIMEOUT, first.terminal()); assertAnalysisEnqueueFailure(first);
        BatchReport second = controller.runBatch(new BatchLimits("no-ready-source-unavailable", 1,
                Duration.ofSeconds(5), Duration.ofMillis(20), Duration.ofMillis(5), 3));
        assertEquals(BatchReport.Terminal.READINESS_TIMEOUT, second.terminal()); assertEquals(2, scans.get()); assertEquals(2, enqueues.get());
        assertTrue(second.detail().contains("retained source custody unavailable"));
        assertEquals(List.of(original.batch().batchId()), second.pendingAnalysisBatchIds()); assertFalse(pending.isDone());
        assertTrue(second.completedAnalyses().isEmpty()); assertEquals(0, fixture.submitted.get()); assertEquals(0, second.committedSavedDays());
    }
    @Test void originalUnknownActionStillAllowsOnlyRetainedIncidentDataAtBatchEnd() throws IOException {
        Fixture fixture = new Fixture(true); CapturedOffline original = capturedOffline("no-ready-unknown-action", BASE.plusSeconds(30));
        var scans = new AtomicInteger(); var enqueues = new AtomicInteger(); var pending = new CompletableFuture<AnalysisCompletion>();
        fixture.retainedSource = () -> { scans.incrementAndGet(); return List.of(original.batch()); };
        fixture.analysis = work -> { assertSame(original.batch(), work); enqueues.incrementAndGet(); return new AnalysisTicket(work.batchId(), pending); };
        SessionController controller = fixture.controller(); BatchReport first = controller.runBatch(limits("no-ready-original-unknown"));
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN, first.terminal()); assertTrue(controller.isQuarantined());
        assertEquals(1, fixture.submitted.get()); assertEquals(1, scans.get()); assertEquals(1, enqueues.get());
        assertEquals(List.of(original.batch().batchId()), first.pendingAnalysisBatchIds()); assertEquals(0, first.committedSavedDays());
        controller.runBatch(limits("no-ready-retained-unknown"));
        assertEquals(1, fixture.submitted.get()); assertEquals(2, scans.get()); assertEquals(1, enqueues.get());
        assertFalse(pending.isDone()); assertTrue(controller.lastReport().orElseThrow().completedAnalyses().isEmpty());
    }
    @Test void oversizedRetainedSourceRefusesBeforeQueueAndPreservesTheActualInnerExit() throws IOException {
        Fixture fixture = new Fixture(false); CapturedOffline original = capturedOffline("no-ready-over-bound", BASE.plusSeconds(30));
        fixture.retainedSource = () -> java.util.Collections.nCopies(RetainedIncidentBatchSource.MAX_BATCHES + 1, original.batch());
        fixture.life = (owner, until) -> new GameLifecycle.Exited(GAME, 23, false, GameLifecycle.TerminalKind.NATURAL_EXIT, REF);
        BatchReport report = fixture.controller().runBatch(limits("no-ready-bound-refusal"));
        assertEquals(BatchReport.Terminal.INNER_EXIT, report.terminal()); assertTrue(report.detail().contains("exit=23"));
        assertTrue(report.detail().contains("finite batch bound")); assertTrue(report.pendingAnalysisBatchIds().isEmpty());
        assertEquals(1L, report.phases().stream().filter(span -> span.phase() == BatchReport.Phase.ANALYSIS_ENQUEUE
                && span.terminal() == BatchReport.PhaseTerminal.FAILED).count());
        assertEquals(0, fixture.observed.get()); assertEquals(0, fixture.submitted.get()); assertEquals(0, report.committedSavedDays());
    }
    @Test void retainedIncidentSourceIsRequiredOnceBeforeAnyBatchWork() {
        Fixture fixture = new Fixture(false); fixture.bindRetainedSource = false; SessionController controller = fixture.controller();
        assertThrows(IllegalArgumentException.class, () -> controller.runBatch(limits("missing-retained-source")));
        assertTrue(fixture.journal.isEmpty()); assertEquals(0, fixture.observed.get()); assertEquals(0, fixture.submitted.get());
        assertThrows(NullPointerException.class, () -> controller.bindRetainedIncidents(null));
        RetainedIncidentBatchSource explicitEmptyFixture = List::of;
        controller.bindRetainedIncidents(explicitEmptyFixture);
        assertThrows(IllegalArgumentException.class, () -> controller.bindRetainedIncidents(explicitEmptyFixture));
        assertEquals(BatchReport.Terminal.INCOMPLETE_MIGRATION, controller.runBatch(limits("bound-retained-source")).terminal());
        assertThrows(IllegalArgumentException.class, () -> controller.bindRetainedIncidents(List::of));
    }
    /** Genuine journal/scan/wire producers with synthetic source DATA; no Native, after or research completion is manufactured. */
    private CapturedOffline capturedOffline(String name, Instant deadline) throws IOException {
        Path root = Files.createDirectory(temporary.resolve(name)); Path original = root.resolve("original-diagnostic-source.json");
        Files.writeString(original, "{\"scope\":\"synthetic-late-observation-diagnostic\"}");
        PlanningRequest base = request(deadline);
        var source = new G2Source(SESSION.machineId(), BASE.toString(), "SYNTHETIC-LATE-OBSERVATION", EpisodeIncidentJournal.measure(original));
        var request = new PlanningRequest(base.before(), source, base.sessionId(), base.deadline(), base.observations());
        var configuration = new EpisodeIncidentJournal.Configuration(Files.createDirectory(root.resolve("incidents")),
                Files.createDirectory(root.resolve("scans")), Clock.fixed(BASE, ZoneOffset.UTC), bytes -> {
                    if (bytes < 0 || bytes > 1_048_576) throw new IOException("finite source-only journal fixture cap");
                }, Optional.empty());
        var binding = new EpisodeIncidentJournal.Binding(request.before(), request.source(), request.sessionId());
        var journal = EpisodeIncidentJournal.initialize(configuration, binding);
        var diagnostic = StrictJson.object().put("schema", "xar.unhandled-native-window-diagnostic/v1")
                .put("kind", "unhandled_event").put("current_event_instance_id", 41).putNull("event_definition_key").putNull("selection")
                .putNull("context").put("diagnostic_reason", "synthetic unavailable native source").put("offline_followup_required", true);
        diagnostic.set("origin", org.xar.ck3.control.g2.planning.ProposalLifecycleCodec.observation(request.before()));
        diagnostic.set("snapshot", StrictJson.parse(DriverJson.encode(request.observations().snapshot())));
        var plan = StrictJson.object().putNull("selected_step"); plan.set("unhandled_native_window_diagnostic", diagnostic);
        journal.captureBlocked(request, OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(plan)), "original late diagnostic"), source.sourceRef());
        var scan = journal.scan(binding); assertEquals(1, scan.diagnosticOnly()); assertEquals(0, scan.incompleteAfter());
        BatchRequest batch = scan.batch().orElseThrow();
        assertEquals(batch, OfflineEventAnalysisWire.decodeBatch(OfflineEventAnalysisWire.encode(batch)));
        return new CapturedOffline(request, journal, configuration, batch);
    }
    @Test void retainedUnacceptedAnalysisRejectsChangedSourcesOnTheNextOrdinaryBatch() {
        Fixture fixture = new Fixture(false);
        var original = new org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest("incident-source-bound", REF, List.of());
        var changed = new org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest(original.batchId(),
                new ExactRef("D:/fixture/changed-incident-manifest.json", 1, "d".repeat(64)), List.of());
        var attempts = new AtomicInteger();
        fixture.observer = (expected, until) -> new Ready(request(until), CheckpointEligibility.SAFE, Optional.of(original), Optional.empty());
        fixture.analysis = work -> {
            assertSame(original, work); attempts.incrementAndGet(); throw new IOException("offline index unavailable");
        };
        SessionController controller = fixture.controller(); controller.runBatch(limits("analysis-original-sources"));
        assertEquals(1, attempts.get());
        fixture.observer = (expected, until) -> new Ready(request(until), CheckpointEligibility.SAFE, Optional.of(changed), Optional.empty());
        BatchReport second = controller.runBatch(limits("analysis-changed-sources"));
        assertEquals(BatchReport.Terminal.INTERNAL_FAILURE, second.terminal());
        assertTrue(second.detail().contains("retained offline incident batch ID changed captured sources"));
        assertEquals(2, attempts.get()); assertTrue(second.pendingAnalysisBatchIds().isEmpty());
        assertTrue(second.completedAnalyses().isEmpty()); assertEquals(0, fixture.submitted.get());
        assertEquals(0, second.committedSavedDays()); assertTrue(controller.isQuarantined());
    }
    @Test void aLatePlannerCannotEnterCompletionOrTurnABatchTimeoutIntoMissingMigration() {
        Fixture fixture=new Fixture(true);fixture.planningDelay=Duration.ofSeconds(6);fixture.blockPlanning=true;
        SessionController controller=fixture.controller();
        BatchReport late=controller.runBatch(limits("late-planner"));
        assertEquals(BatchReport.Terminal.WALL_TIMEOUT,late.terminal());
        assertEquals(0,fixture.planningPublications);assertEquals(0,fixture.submitted.get());
        assertTrue(late.turns().isEmpty());assertEquals(0,late.committedSavedDays());assertFalse(controller.isQuarantined());
        fixture.planningDelay=Duration.ZERO;fixture.blockPlanning=false;
        BatchReport next=controller.runBatch(limits("late-planner-next"));
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,next.terminal());
        assertEquals(1,fixture.planningPublications);assertEquals(1,fixture.submitted.get());
    }
    @Test void aLatePlanningCompletionKeepsTheWallTimeoutAndAllowsTheNextFiniteBatch() {
        Fixture fixture=new Fixture(true);fixture.planningCompletionDelay=Duration.ofSeconds(6);fixture.blockPlanning=true;
        SessionController controller=fixture.controller();
        BatchReport late=controller.runBatch(limits("late-completion"));
        assertEquals(BatchReport.Terminal.WALL_TIMEOUT,late.terminal());
        assertEquals(1,fixture.planningPublications);assertEquals(0,fixture.submitted.get());
        assertTrue(late.turns().isEmpty());assertEquals(0,late.committedSavedDays());assertFalse(controller.isQuarantined());
        fixture.planningCompletionDelay=Duration.ZERO;fixture.blockPlanning=false;
        BatchReport next=controller.runBatch(limits("late-completion-next"));
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,next.terminal());
        assertEquals(2,fixture.planningPublications);assertEquals(1,fixture.submitted.get());
    }
    @Test void aLateSuccessfulPlanningScopeCannotTurnABatchTimeoutIntoMissingMigration() {
        Fixture fixture=new Fixture(true);fixture.planningScopeExitDelay=Duration.ofSeconds(6);fixture.blockPlanning=true;
        SessionController controller=fixture.controller();
        BatchReport late=controller.runBatch(limits("late-scope-return"));
        assertEquals(BatchReport.Terminal.WALL_TIMEOUT,late.terminal());
        assertEquals(1,fixture.planningPublications);assertEquals(0,fixture.submitted.get());
        assertEquals(0,fixture.scopeDepth);assertTrue(late.turns().isEmpty());assertEquals(0,late.committedSavedDays());
        assertFalse(controller.isQuarantined());
        assertEquals(JournalKind.BATCH_DEFERRED,fixture.journal.getLast().kind());
    }
    @Test void aLateFailedPlanningScopeRetainsItsActualWriterUnknown() {
        Fixture fixture=new Fixture(true);fixture.planningScopeExitDelay=Duration.ofSeconds(6);fixture.failScopePublication=true;
        SessionController controller=fixture.controller();
        BatchReport failed=controller.runBatch(limits("late-scope-failure"));
        assertEquals(BatchReport.Terminal.WRITER_UNKNOWN,failed.terminal());
        assertEquals(1,fixture.planningPublications);assertEquals(0,fixture.submitted.get());
        assertEquals(0,fixture.scopeDepth);assertTrue(controller.isQuarantined());
        assertEquals(1,fixture.journal.size());assertEquals(JournalKind.BATCH_STARTED,fixture.journal.getFirst().kind());
        assertEquals(0,failed.committedSavedDays());
    }
    @Test void actualPlanningCompletionCanBlockBeforeAnySelectedActionIsDispatched() {
        Fixture fixture=new Fixture(true);fixture.blockPlanning=true;
        BatchReport result=fixture.controller().runBatch(limits("completion-blocked"));
        assertEquals(BatchReport.Terminal.INCOMPLETE_MIGRATION,result.terminal());assertTrue(result.detail().contains("actual plan publication blocked"));
        assertEquals(1,fixture.planningPublications);assertEquals(0,fixture.submitted.get());assertTrue(fixture.completedReceipts.isEmpty());
    }
    @Test void unknownReceiptIsPublishedToTheRealCompletionPortOnceWithoutReplayOrSave() {
        Fixture fixture=new Fixture(true);BatchReport result=fixture.controller().runBatch(limits("completion-unknown"));
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,result.terminal());assertEquals(1,fixture.completedReceipts.size());
        assertSame(result.turns().getFirst().receipt(),fixture.completedReceipts.getFirst());assertEquals(0,result.committedSavedDays());
    }
    @Test void aPublishedHeadForcesAFreshPlanBeforeTheOldSelectedCommandCanExecute() {
        Fixture fixture=new Fixture(true);fixture.publishFirstPlan=true;
        BatchReport result=fixture.controller().runBatch(limits("published-replan"));
        assertEquals(BatchReport.Terminal.INCOMPLETE_MIGRATION,result.terminal());assertEquals(2,fixture.planningPublications);
        assertEquals(2,fixture.observed.get());assertEquals(0,fixture.submitted.get());assertTrue(result.turns().isEmpty());
    }

    @Test void actualTerminalUnknownKeepsItsDistinctIdentityAndNeverReplaysOrUsesOrdinaryPlanning() {
        Fixture fixture=new Fixture(false);LifecycleIdentity terminal=terminalIdentity();
        fixture.observer=(expected,until)->{fixture.observed.incrementAndGet();fixture.terminalOriginal=terminalCommand(terminal,until);return new TerminalReady(terminal,new TerminalAction(fixture.terminalOriginal));};
        SessionController controller=fixture.controller();BatchReport result=controller.runBatch(limits("terminal-unknown"));
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,result.terminal());assertEquals(1,fixture.submitted.get());
        assertTrue(result.turns().isEmpty());assertTrue(result.reconciliations().isEmpty());assertEquals(1,result.lifecycleTurns().size());
        var actual=result.lifecycleTurns().getFirst();assertEquals(terminal,actual.current());assertFalse(actual.reconciliation());
        assertEquals(fixture.terminalOriginal,actual.receipt().command());assertThrows(IllegalStateException.class,actual.receipt().command()::before);
        assertEquals(actual.receipt().command(),ActionCodec.decodeCommand(ActionCodec.encodeCommand(actual.receipt().command())));
        assertEquals(0,fixture.planningPublications);assertTrue(fixture.completedReceipts.isEmpty());assertEquals(0,fixture.episodeCalls);assertEquals(0,result.committedSavedDays());
        controller.runBatch(limits("terminal-after-unknown"));assertEquals(1,fixture.submitted.get());assertEquals(1,fixture.observed.get());
    }
    @Test void originalTerminalUnknownUsesOnlyReadOnlyReconciliationAndRetainsTheCanonicalBody() {
        Fixture fixture=new Fixture(false);fixture.reconcileExisting=true;LifecycleIdentity terminal=terminalIdentity();
        fixture.terminalOriginal=terminalCommand(terminal,BASE.plusSeconds(1));
        fixture.observer=(expected,until)->new TerminalReady(terminal,new TerminalReconciliation(fixture.terminalOriginal.actionId()));
        BatchReport report=fixture.controller().runBatch(limits("terminal-reconcile"));
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,report.terminal());assertEquals(0,fixture.submitted.get());assertEquals(1,fixture.reconciled.get());
        assertEquals(1,report.lifecycleTurns().size());assertTrue(report.lifecycleTurns().getFirst().reconciliation());
        assertEquals(BASE.plusSeconds(1),report.lifecycleTurns().getFirst().receipt().command().deadline());
        assertEquals(0,fixture.planningPublications);assertEquals(0,fixture.episodeCalls);assertEquals(0,report.committedSavedDays());
    }
    @Test void publicRequestedTerminalOperationRejectsAnotherSelectedOperationBeforeAnyDispatch() {
        Fixture fixture=new Fixture(false);var terminal=terminalIdentity();
        fixture.observer=(owner,until)->new TerminalReady(terminal,new TerminalAction(terminalCommand(terminal,until)));
        var report=fixture.controller().terminalTurn(LifecycleExpectedPostcondition.Operation.START_NEXT_EPISODE,Optional.empty(),BASE.plusSeconds(5)).execution();
        assertEquals(BatchReport.Terminal.ACTION_REJECTED,report.terminal());
        assertTrue(report.detail().contains("differs from requested"));assertEquals(0,fixture.submitted.get());
        assertEquals(0,fixture.reconciled.get());assertEquals(0,fixture.planningPublications);assertEquals(0,fixture.episodeCalls);
        assertTrue(report.turns().isEmpty());assertTrue(report.lifecycleTurns().isEmpty());assertEquals(0,report.committedSavedDays());
    }
    @Test void publicTerminalRequestDoesNotEnterOrdinaryPlannerOrInitialSave() {
        Fixture fixture=new Fixture(true);fixture.withBaseline=false;
        var report=fixture.controller().terminalTurn(LifecycleExpectedPostcondition.Operation.START_NEXT_EPISODE,Optional.empty(),BASE.plusSeconds(5)).execution();
        assertEquals(BatchReport.Terminal.ACTION_REJECTED,report.terminal());assertEquals(1,fixture.observed.get());
        assertEquals(0,fixture.planningPublications);assertEquals(0,fixture.submitted.get());assertTrue(report.lastSavedPair().isEmpty());
        assertTrue(report.lastPlan().isEmpty());assertTrue(report.phases().stream().noneMatch(span->span.phase()==BatchReport.Phase.CHECKPOINT));
    }
    @Test void requestedRevisionUsesTheSameSelectedPublicFrameAndNeverTheNativeRevision() {
        Fixture fixture=new Fixture(false);var terminal=terminalIdentity(BigInteger.valueOf(7));
        fixture.observer=(owner,until)->new TerminalReady(terminal,new TerminalAction(terminalCommand(terminal,until,LifecycleExpectedPostcondition.Operation.START_NEXT_EPISODE)));
        var report=fixture.controller().terminalTurn(LifecycleExpectedPostcondition.Operation.START_NEXT_EPISODE,Optional.of(BigInteger.TWO),BASE.plusSeconds(5)).execution();
        assertEquals(BatchReport.Terminal.ACTION_REJECTED,report.terminal());assertTrue(report.detail().contains("revision"));
        assertEquals(BigInteger.TWO,terminal.frame().nativeRevision());assertEquals(BigInteger.valueOf(7),terminal.frame().revision());
        assertEquals(0,fixture.submitted.get());assertEquals(0,fixture.reconciled.get());assertTrue(report.lifecycleTurns().isEmpty());
    }
    @Test void exactRequestedOperationAndRevisionReachTheSameCoordinatorOnceAndUnknownNeverRepeats() {
        Fixture fixture=new Fixture(false);var terminal=terminalIdentity(BigInteger.valueOf(7));
        fixture.observer=(owner,until)->{fixture.observed.incrementAndGet();fixture.terminalOriginal=terminalCommand(terminal,until,LifecycleExpectedPostcondition.Operation.START_NEXT_EPISODE);return new TerminalReady(terminal,new TerminalAction(fixture.terminalOriginal));};
        var controller=fixture.controller();var report=controller.terminalTurn(LifecycleExpectedPostcondition.Operation.START_NEXT_EPISODE,Optional.of(BigInteger.valueOf(7)),BASE.plusSeconds(5)).execution();
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,report.terminal());assertEquals(1,fixture.submitted.get());assertEquals(1,fixture.observed.get());
        var original=report.lifecycleTurns().getFirst().receipt();assertEquals(fixture.terminalOriginal,original.command());
        assertEquals(original.command(),ActionCodec.decodeCommand(ActionCodec.encodeCommand(original.command())));
        controller.terminalTurn(LifecycleExpectedPostcondition.Operation.START_NEXT_EPISODE,Optional.of(BigInteger.valueOf(7)),BASE.plusSeconds(5));
        assertEquals(1,fixture.submitted.get());assertEquals(1,fixture.observed.get());assertEquals(0,fixture.episodeCalls);
        assertEquals(0,fixture.planningPublications);assertEquals(0,report.committedSavedDays());
    }
    @Test void requestedTerminalReconciliationCannotGuessItsOperationOrReplaceTheRetainedUnknown() {
        Fixture fixture=new Fixture(false);fixture.reconcileExisting=true;var terminal=terminalIdentity();
        fixture.terminalOriginal=terminalCommand(terminal,BASE.plusSeconds(1));
        fixture.observer=(owner,until)->new TerminalReady(terminal,new TerminalReconciliation(fixture.terminalOriginal.actionId()));
        var controller=fixture.controller();var rejected=controller.terminalTurn(LifecycleExpectedPostcondition.Operation.START_NEXT_EPISODE,Optional.empty(),BASE.plusSeconds(5)).execution();
        assertEquals(BatchReport.Terminal.ACTION_REJECTED,rejected.terminal());assertEquals(0,fixture.reconciled.get());assertEquals(0,fixture.submitted.get());
        var original=controller.autoTurn(BASE.plusSeconds(5)).execution();
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,original.terminal());assertEquals(1,fixture.reconciled.get());assertEquals(0,fixture.submitted.get());
        assertEquals(fixture.terminalOriginal,original.lifecycleTurns().getFirst().receipt().command());
    }
    @Test void privateChildOrInvalidTypedRevisionRefusesBeforeObservationAndJournal() {
        Fixture fixture=new Fixture(false);var controller=fixture.controller();
        assertThrows(IllegalArgumentException.class,()->controller.terminalTurn(LifecycleExpectedPostcondition.Operation.CLOSE_DEATH_MODAL,Optional.empty(),BASE.plusSeconds(5)));
        assertThrows(IllegalArgumentException.class,()->controller.terminalTurn(LifecycleExpectedPostcondition.Operation.START_NEXT_EPISODE,Optional.of(BigInteger.valueOf(-1)),BASE.plusSeconds(5)));
        assertThrows(NullPointerException.class,()->controller.terminalTurn(LifecycleExpectedPostcondition.Operation.START_NEXT_EPISODE,null,BASE.plusSeconds(5)));
        assertEquals(0,fixture.observed.get());assertEquals(0,fixture.submitted.get());assertTrue(fixture.journal.isEmpty());
    }
    @Test void missingActualTerminalDecisionEvidenceBlocksWithoutEnteringOrdinaryPlanningOrSubmission() {
        Fixture fixture=new Fixture(false);fixture.observer=(owner,until)->new TerminalReady(terminalIdentity(),new TerminalBlocked("actual successor source absent",List.of(REF)));
        BatchReport report=fixture.controller().runBatch(limits("terminal-blocked"));
        assertEquals(BatchReport.Terminal.INCOMPLETE_MIGRATION,report.terminal());assertTrue(report.detail().contains("actual successor source absent"));
        assertEquals(List.of(REF),((TerminalBlocked)report.lastTerminalObservation().orElseThrow().decision()).evidence());assertTrue(report.lastPlan().isEmpty());
        assertEquals(0,fixture.planningPublications);assertEquals(0,fixture.submitted.get());assertTrue(report.lifecycleTurns().isEmpty());
        assertThrows(IllegalArgumentException.class,()->new TerminalBlocked("absent evidence",List.of()));
        var ordinary=command(request(BASE.plusSeconds(5)));assertThrows(IllegalArgumentException.class,()->new TerminalAction(ordinary));
    }
    @Test void terminalObservationReconcilesAnOriginalOrdinaryUnknownWithoutInventingATerminalCommandOrCycle() {
        Fixture fixture=new Fixture(false);fixture.reconcileExisting=true;LifecycleIdentity terminal=terminalIdentity();
        fixture.observer=(owner,until)->new TerminalReady(terminal,new TerminalReconciliation("original-action"));
        BatchReport report=fixture.controller().runBatch(limits("terminal-original-ordinary"));
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,report.terminal());assertEquals(0,fixture.submitted.get());assertEquals(1,fixture.reconciled.get());
        assertEquals(1,report.lifecycleTurns().size());var actual=report.lifecycleTurns().getFirst();
        assertTrue(actual.reconciliation());assertInstanceOf(CommandOrigin.Gameplay.class,actual.receipt().command().origin());
        assertEquals(terminal,actual.current());assertTrue(report.turns().isEmpty());assertEquals(1,fixture.completedReceipts.size());
        assertEquals(0,fixture.planningPublications);assertEquals(0,fixture.episodeCalls);assertEquals(0,report.committedSavedDays());
    }
    @Test void actualScopePublicationDiscardsTheWholeCapturedPlanAndReobservesBeforeAnyDispatch() {
        Fixture fixture=new Fixture(true);fixture.publishFirstScope=true;
        BatchReport report=fixture.controller().runBatch(limits("scope-publication"));
        assertEquals(BatchReport.Terminal.INCOMPLETE_MIGRATION,report.terminal());assertEquals(2,fixture.scopeEntries);
        assertEquals(2,fixture.observed.get());assertEquals(2,fixture.planningPublications);assertEquals(0,fixture.submitted.get());
        assertTrue(report.turns().isEmpty());assertEquals(0,fixture.scopeDepth);
    }
    @Test void aFailedScopeReadPublicationIsWriterUnknownAndFinalizationDoesNotWriteAgain() {
        Fixture fixture=new Fixture(true);fixture.failScopePublication=true;
        BatchReport report=fixture.controller().runBatch(limits("scope-writer-unknown"));
        assertEquals(BatchReport.Terminal.WRITER_UNKNOWN,report.terminal());assertEquals(1,fixture.scopeEntries);
        assertEquals(1,fixture.journal.size());assertEquals(JournalKind.BATCH_STARTED,fixture.journal.getFirst().kind());
        assertEquals(0,fixture.submitted.get());assertTrue(report.turns().isEmpty());assertEquals(0,fixture.scopeDepth);
    }
    @Test void actualDomainCheckpointRequirementDoesNotCreateAnImplicitSaveInPublicAutoTurn() {
        Fixture fixture=new Fixture(true);fixture.requireCheckpoint=true;
        BatchReport report=fixture.controller().autoTurn(BASE.plusSeconds(5)).execution();
        assertEquals(BatchReport.Terminal.CHECKPOINT_DEFERRED,report.terminal());assertEquals(1,fixture.planningPublications);
        assertEquals(0,fixture.submitted.get());assertEquals(0,report.committedSavedDays());
        assertEquals("save-initial",report.lastSavedPair().orElseThrow().saveActionId());assertTrue(report.turns().isEmpty());
    }
    @Test void theTypedActualReadPublicationRefreshReobservesWithoutInventingAnActionOutcomeOrRetryingUnknown() {
        Fixture fixture=new Fixture(true);fixture.readRefreshBeforeDispatch=true;
        BatchReport report=fixture.controller().runBatch(limits("read-refresh-before-dispatch"));
        assertTrue(fixture.readRefreshIssued);assertEquals(2,fixture.observed.get());assertEquals(2,fixture.planningPublications);
        assertEquals(1,fixture.submitted.get());assertEquals(1,report.turns().size());assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,report.terminal());
        assertEquals(1,fixture.completedReceipts.size());assertSame(report.turns().getFirst().receipt(),fixture.completedReceipts.getFirst());assertEquals(0,report.committedSavedDays());
    }
    @Test void aReadPublicationWithAnActualUnresolvedParentReconcilesOnlyThatParentBeforeAnyNewObservationOrAction() {
        Fixture fixture=new Fixture(true);fixture.readRefreshBeforeDispatch=true;fixture.refreshHasParent=true;
        BatchReport report=fixture.controller().runBatch(limits("read-refresh-unresolved-parent"));
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,report.terminal());assertEquals(1,fixture.observed.get());assertEquals(1,fixture.planningPublications);
        assertEquals(0,fixture.submitted.get());assertEquals(1,fixture.reconciled.get());assertTrue(report.turns().isEmpty());assertTrue(report.lastPlan().isEmpty());
        assertEquals(1,report.readPublicationReconciliations().size());assertEquals(fixture.readParentOriginal,report.readPublicationReconciliations().getFirst().originalReceipt().command());
        assertEquals(1,fixture.completedReceipts.size());assertEquals(0,report.committedSavedDays());
    }
    @Test void pendingUiDataCannotAuthorizeTheDefaultContinuationOrEnterPlanningSaveOrANewParent() {
        Fixture fixture=new Fixture(false);var pending=pendingUiData(BASE.plusSeconds(1));
        fixture.pendingProbe=(owner,until)->Optional.of(pending);
        var controller=fixture.controller();var report=controller.autoTurn(BASE.plusSeconds(5)).execution();
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,report.terminal());assertTrue(controller.isQuarantined());
        assertTrue(report.lifecycleTurns().isEmpty());assertEquals(0,fixture.scopeEntries);assertEquals(0,fixture.observed.get());
        assertEquals(0,fixture.submitted.get());assertEquals(0,fixture.reconciled.get());assertEquals(0,fixture.episodeCalls);
        assertEquals(0,report.committedSavedDays());assertEquals("save-initial",report.lastSavedPair().orElseThrow().saveActionId());
    }
    @Test void sameControllerQuarantineOnlyAllowsTheFiniteSourceProbeAndRetainsUnknownWithoutAReplacementParent() {
        Fixture fixture=new Fixture(false);var pending=pendingUiData(BASE.plusSeconds(1));
        fixture.observer=(owner,until)->new TerminalReady(pending.token().originalParent().lifecycleBefore(),new TerminalAction(pending.token().originalParent()));
        var controller=fixture.controller();var first=controller.autoTurn(BASE.plusSeconds(5)).execution();
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,first.terminal());assertEquals(1,fixture.submitted.get());
        int scopes=fixture.scopeEntries;
        fixture.pendingProbe=(owner,until)->{assertEquals(0,fixture.scopeDepth);return Optional.of(pending);};
        // Control DATA only. This port retains UNKNOWN and cannot mint the Root private finalized proof.
        fixture.continuationProvider=Optional.of(token->new CompositeContinuationReport(first.lifecycleTurns().getFirst().receipt(),List.of(),
                CompositeContinuationReport.Disposition.NO_NEW_CHILD_ATTEMPT));
        var second=controller.autoTurn(BASE.plusSeconds(5)).execution();
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,second.terminal());assertEquals(1,fixture.submitted.get());
        assertEquals(scopes,fixture.scopeEntries);assertEquals(0,fixture.reconciled.get());assertEquals(0,fixture.episodeCalls);
        var turn=second.lifecycleTurns().getFirst();assertFalse(turn.reconciliation());assertSame(first.lifecycleTurns().getFirst().receipt(),turn.receipt());
        assertEquals(CompositeContinuationReport.Disposition.NO_NEW_CHILD_ATTEMPT,turn.successorUiContinuation().orElseThrow().actual().disposition());
        assertTrue(controller.isQuarantined());assertFalse(second.dirtySinceSave());assertEquals(0,second.committedSavedDays());
        fixture.pendingProbe=(owner,until)->Optional.empty();int calls=fixture.continuationCalls;
        var third=controller.autoTurn(BASE.plusSeconds(5)).execution();
        assertEquals(BatchReport.Terminal.INTERNAL_FAILURE,third.terminal());assertEquals(calls,fixture.continuationCalls);
        assertEquals(1,fixture.submitted.get());assertEquals(scopes,fixture.scopeEntries);
    }
    @Test void callerDeadlineAndPublicDesiredOperationCannotBeReplacedByPendingUiContinuation() {
        Fixture fixture=new Fixture(false);fixture.pendingProbe=(owner,until)->Optional.of(pendingUiData(BASE.plusSeconds(6)));
        var controller=fixture.controller();var expired=controller.autoTurn(BASE.plusSeconds(5)).execution();
        assertEquals(BatchReport.Terminal.INTERNAL_FAILURE,expired.terminal());assertEquals(0,fixture.continuationCalls);assertEquals(0,fixture.scopeEntries);
        var requested=controller.terminalTurn(LifecycleExpectedPostcondition.Operation.START_NEXT_EPISODE,Optional.empty(),BASE.plusSeconds(5)).execution();
        assertEquals(BatchReport.Terminal.INTERNAL_FAILURE,requested.terminal());assertEquals(0,fixture.continuationCalls);assertEquals(0,fixture.submitted.get());
    }
    @Test void pendingUiReportSerdePreservesAttemptDispositionAndRejectsReadonlyOrLossyClaims() {
        var pending=pendingUiData(BASE.plusSeconds(1));var parent=pending.token().originalParent();
        var receipt=new ActionReceipt(1,1,parent,ActionCodec.bodySha256(parent),new ActionState.Unknown(Optional.empty(),Optional.empty(),"retained original",List.of(REF)));
        var pass=new BatchReport.SuccessorUiContinuation(pending.token().kind(),new CompositeContinuationReport(receipt,List.of(),
                CompositeContinuationReport.Disposition.NO_NEW_CHILD_ATTEMPT),REF,REF,REF);
        var encoded=SuccessorUiContinuationJson.encode(pass);
        SuccessorUiContinuationJson.validate(StrictJson.parse(StrictJson.canonical(encoded,262_144)));
        assertFalse(encoded.get("new_parent_submitted").booleanValue());assertTrue(encoded.get("new_child_attempts").isEmpty());
        for(String field:List.of("new_parent_submitted","disposition","canonical_domain")) {
            var missing=encoded.deepCopy();missing.remove(field);assertThrows(RuntimeException.class,()->SuccessorUiContinuationJson.validate(missing));
        }
        var wrong=encoded.deepCopy();wrong.put("disposition","NEW_CHILD_ATTEMPT");assertThrows(IllegalArgumentException.class,()->SuccessorUiContinuationJson.validate(wrong));
        var readonly=encoded.deepCopy();readonly.put("new_parent_submitted",true);assertThrows(IllegalArgumentException.class,()->SuccessorUiContinuationJson.validate(readonly));
        assertThrows(IllegalArgumentException.class,()->new BatchReport.LifecycleTurn(1,parent.lifecycleBefore(),receipt,true,Optional.of(pass)));
        assertThrows(IllegalArgumentException.class,()->new PendingSuccessorUi(new PendingUiData(terminalCommand(terminalIdentity(),BASE.plusSeconds(1)),
                pending.token().obligation(),BASE.plusSeconds(1),CompositeContinuationToken.Kind.SUCCESSOR_UI_CLOSE)));
    }
    @Test void publicPendingOnlyMissingSourceNeverFallsIntoOrdinaryOrTerminalPlanningOrSave() {
        Fixture fixture=new Fixture(true);var controller=fixture.controller();
        var report=controller.pendingSuccessorUiTurn(BASE.plusSeconds(5)).execution();
        assertEquals(BatchReport.Terminal.ACTION_REJECTED,report.terminal());assertFalse(controller.isQuarantined());
        assertEquals(0,fixture.scopeEntries);assertEquals(0,fixture.observed.get());assertEquals(0,fixture.submitted.get());
        assertTrue(fixture.journal.isEmpty());assertTrue(report.lifecycleTurns().isEmpty());assertEquals(0,fixture.episodeCalls);
        assertEquals(0,report.committedSavedDays());assertEquals("save-initial",controller.savedPair().orElseThrow().saveActionId());
    }
    @Test void publicPendingOnlyRetainsOneOriginalUnknownAndReturnsWithoutOrdinaryWork() {
        Fixture fixture=new Fixture(true);var pending=pendingUiData(BASE.plusSeconds(1));
        fixture.pendingProbe=(owner,until)->Optional.of(pending);
        fixture.continuationProvider=Optional.of(token->{var parent=token.originalParent();
            var retained=new ActionReceipt(1,1,parent,ActionCodec.bodySha256(parent),
                    new ActionState.Unknown(Optional.empty(),Optional.empty(),"original pending remains unresolved",List.of(REF)));
            return new CompositeContinuationReport(retained,List.of(),CompositeContinuationReport.Disposition.NO_NEW_CHILD_ATTEMPT);
        });
        var controller=fixture.controller();var report=controller.pendingSuccessorUiTurn(BASE.plusSeconds(5)).execution();
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,report.terminal());assertTrue(controller.isQuarantined());
        assertEquals(1,fixture.continuationCalls);assertEquals(1,report.lifecycleTurns().size());
        assertEquals(pending.token().originalParent(),report.lifecycleTurns().getFirst().receipt().command());
        assertEquals(0,fixture.scopeEntries);assertEquals(0,fixture.observed.get());assertEquals(0,fixture.submitted.get());
        assertEquals(0,fixture.reconciled.get());assertEquals(0,fixture.episodeCalls);assertFalse(report.dirtySinceSave());assertEquals(0,report.committedSavedDays());
    }
    @Test void privatePendingAdmissionLostAfterBatchCommitStaysQuarantinedWithoutOrdinaryFallback() {
        Fixture fixture=new Fixture(true);var pending=pendingUiData(BASE.plusSeconds(1));var probes=new AtomicInteger();
        fixture.pendingProbe=(owner,until)->probes.incrementAndGet()==1?Optional.of(pending):Optional.empty();
        var controller=fixture.controller();var report=controller.pendingSuccessorUiTurn(BASE.plusSeconds(5)).execution();
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN,report.terminal());assertTrue(controller.isQuarantined());assertEquals(2,probes.get());
        assertEquals(0,fixture.continuationCalls);assertEquals(0,fixture.scopeEntries);assertEquals(0,fixture.submitted.get());
        assertEquals(JournalKind.BATCH_STARTED,fixture.journal.getFirst().kind());assertEquals(JournalKind.BATCH_INTERRUPTED,fixture.journal.getLast().kind());
        assertEquals(0,report.committedSavedDays());assertEquals(0,fixture.episodeCalls);
    }
    private record PendingUiData(ActionCommand originalParent,SuccessorUiObligation obligation,Instant deadline,
            CompositeContinuationToken.Kind kind) implements NaturalSuccessionPreparation.PendingToken {
        @Override public ExactRef canonicalDomain(){return REF;}
        @Override public ExactRef actualPublishedDriver(){return REF;}
        @Override public ExactRef canonicalPublicationProof(){return REF;}
        @Override public List<ExactRef> evidence(){return List.of(REF);}
    }
    private static PendingSuccessorUi pendingUiData(Instant deadline) {
        var old=terminalIdentity();var predecessor=new LifecycleIdentity(old.machineId(),old.game(),old.sessionId(),old.connectionGeneration(),
                old.subject(),old.frame(),new LifecycleIdentity.Character(BigInteger.valueOf(40000),true),LifecycleIdentity.TerminalReason.CHANGED,old.evidence(),old.observedAt());
        var parent=terminalCommand(predecessor,BASE.plusSeconds(1),LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR);
        var binding=new SuccessorUiObligation.Binding(predecessor,BigInteger.valueOf(40000),"episode-2","e".repeat(64),"f".repeat(64),
                parent.actionId(),ActionCodec.bodySha256(parent),REF,REF,REF,BASE);
        var obligation=new SuccessorUiObligation(binding,SuccessorUiObligation.Phase.PENDING,Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty());
        return new PendingSuccessorUi(new PendingUiData(parent,obligation,deadline,CompositeContinuationToken.Kind.SUCCESSOR_UI_CLOSE));
    }
    private static LifecycleIdentity terminalIdentity() {
        return terminalIdentity(BigInteger.TWO);
    }
    private static LifecycleIdentity terminalIdentity(BigInteger publicRevision) {
        return new LifecycleIdentity(SESSION.machineId(),GAME,SESSION.sessionId(),BigInteger.ONE,
                new LifecycleIdentity.Subject(BigInteger.valueOf(29829),"episode-1",1,2),
                new LifecycleIdentity.Frame("terminal-native",publicRevision,BigInteger.valueOf(2),BigInteger.valueOf(24024),true,false),
                new LifecycleIdentity.Null(),LifecycleIdentity.TerminalReason.MISSING,
                new LifecycleIdentity.Evidence(REF,new ExactRef("D:/fixture/hello",1,"b".repeat(64)),new ExactRef("D:/fixture/manifest",1,"c".repeat(64)),
                        new ExactRef("D:/fixture/original-driver",1,"d".repeat(64)),new ExactRef("D:/fixture/source-proof",1,"e".repeat(64))),BASE);
    }
    private static ActionCommand terminalCommand(LifecycleIdentity identity,Instant deadline) {
        return terminalCommand(identity,deadline,LifecycleExpectedPostcondition.Operation.DEATH_TERMINAL);
    }
    private static ActionCommand terminalCommand(LifecycleIdentity identity,Instant deadline,LifecycleExpectedPostcondition.Operation operation) {
        var source=new G2Source(SESSION.machineId(),BASE.toString(),"fixture-build",REF);
        var flags=List.<ExpectedValue>of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"),false),new ExpectedBoolean(new FieldKey("timeline.advance_verified"),false),new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"),false));
        return new ActionCommand("original-terminal",new CommandOrigin.LifecycleTerminal(identity),source,SESSION.sessionId(),operation.key(),new OpportunityJson.Obj(Map.of()),
                new CommandExpectation.LifecycleTerminal(new LifecycleExpectedPostcondition(identity,source,"fixture-lifecycle/v1",operation,flags)),
                new JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),deadline);
    }
    private static BatchLimits limits(String id) { return new BatchLimits(id, 2, Duration.ofSeconds(5), Duration.ofSeconds(1), Duration.ofMillis(5), 3); }
    private static PlanningRequest request(Instant deadline) {
        var before = new ObservationIdentity(SESSION.machineId(), GAME,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.ONE, BigInteger.valueOf(24000)), "frame-1", BigInteger.ONE, "episode-1"), 1);
        var snapshot = OpportunityJson.object(OpportunityJson.parse(("{\"paused\":true,\"map_ready\":true,\"revision\":1,\"native_revision\":1,\"date_raw\":24000,"
                + "\"snapshot_id\":\"frame-1\",\"episode_run_id\":\"episode-1\",\"played_character\":{\"character_id\":29829},\"active_wars\":[],\"player_armies\":[]}").getBytes(StandardCharsets.UTF_8)), "fixture");
        var observation = new PlanningObservation(snapshot, List.of(), Set.of(new OperationKey("fixture-world-action")), Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false);
        return new PlanningRequest(before, new G2Source(SESSION.machineId(), BASE.toString(), "fixture-build", REF), SESSION.sessionId(), deadline, observation);
    }
    private static ActionCommand command(PlanningRequest request) {
        return command(request, "action-1");
    }
    private static ActionCommand command(PlanningRequest request, String id) {
        return new ActionCommand(id, request.before(), request.source(), request.sessionId(), new OperationKey("fixture-world-action"), new OpportunityJson.Obj(Map.of()),
                new ExpectedPostcondition(1, request.before(), request.source(), "fixture-observer/v1", List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true))),
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), request.deadline());
    }
    private static final class TestClock implements SessionClock {
        long nanos;
        @Override public Tick now() { nanos += 1_000_000; return new Tick(nanos, BASE.plusNanos(nanos)); }
        @Override public void waitFor(Duration duration) { nanos += duration.toNanos(); }
    }
    private static final class Fixture {
        final TestClock time = new TestClock(); final AtomicInteger observed = new AtomicInteger(); final AtomicInteger submitted = new AtomicInteger(); final AtomicInteger reconciled = new AtomicInteger();
        final List<JournalInput> journal = new ArrayList<>(); final boolean completePlanner; boolean withBaseline = true; boolean reconcileExisting; boolean cycleAvailable = true;
        int planningPublications,episodeCalls,scopeEntries,scopeDepth;ActionCommand terminalOriginal,readParentOriginal;boolean blockPlanning,publishFirstPlan,publishFirstScope,failScopePublication,requireCheckpoint,readRefreshBeforeDispatch,readRefreshIssued,refreshHasParent;final List<ActionReceipt> completedReceipts=new ArrayList<>();
        int continuationCalls;
        Duration planningDelay=Duration.ZERO,planningCompletionDelay=Duration.ZERO,planningScopeExitDelay=Duration.ZERO;
        java.util.function.BiFunction<SessionIdentity,Instant,Optional<PendingSuccessorUi>> pendingProbe=(owner,until)->Optional.empty();
        Optional<java.util.function.Function<CompositeContinuationToken,CompositeContinuationReport>> continuationProvider=Optional.empty();
        final org.xar.ck3.control.application.planning.OrdinaryPlanCompletion.PlanningScope completion=new org.xar.ck3.control.application.planning.OrdinaryPlanCompletion.PlanningScope() {
            @Override public <T> ScopeResult<T> inPlanningScope(ScopeWork<T> work) throws IOException,InterruptedException {
                assertEquals(0,scopeDepth);scopeEntries++;scopeDepth++;
                try{T result=work.run();time.waitFor(planningScopeExitDelay);if(failScopePublication)throw new IOException("actual read publication completion lost");return new ScopeResult<>(result,publishFirstScope&&scopeEntries==1?Optional.of(publication()):Optional.empty());}
                finally{scopeDepth--;}
            }
            @Override public PlanningDisposition afterPlanning(PlanningRequest original,org.xar.ck3.control.application.planning.PlanningResult planned) {
                assertEquals(1,scopeDepth);
                time.waitFor(planningCompletionDelay);
                planningPublications++;
                if(requireCheckpoint)return new CheckpointRequired(confirmedFocus(original),List.of(REF));
                if(publishFirstPlan&&planningPublications==1)return publication();
                return blockPlanning||publishFirstPlan||publishFirstScope&&scopeEntries>1?new Blocked("actual fixture publication unavailable",List.of(REF)):new Unchanged("no fixture publication");
            }
            @Override public ExecutionDisposition afterExecution(ActionReceipt actual) {assertEquals(0,scopeDepth);completedReceipts.add(actual);return new Unchanged("actual fixture receipt consumed");}
        };
        LifecyclePort life = (expected, until) -> new GameLifecycle.Running(GAME, REF);
        ObservationPort observer = (expected, until) -> { observed.incrementAndGet(); return new Ready(request(until), CheckpointEligibility.SAFE, Optional.empty(), Optional.of(semantic(request(until)))); };
        BatchJournal writer = new BatchJournal() {
            @Override public JournalCommit commit(JournalInput input) { journal.add(input); return new JournalCommit(REF, 0); }
            @Override public Optional<CompletedCycleProof> cycleProof(SessionIdentity owner, SemanticEvidence semantic) {
                return cycleAvailable ? Optional.of(new CompletedCycleProof(0, semantic, "d".repeat(64))) : Optional.empty();
            }
        };
        OfflineAnalysisPort analysis = work -> { throw new AssertionError("no captured incident expected"); };
        RetainedIncidentBatchSource retainedSource = List::of;
        boolean bindRetainedSource = true;
        Fixture(boolean completePlanner) { this.completePlanner = completePlanner; }
        private ActionReceipt confirmedFocus(PlanningRequest original) {
            var selected=command(original,"focus-original");
            var guard=new GuardEvidence(original.before(),original.source(),original.sessionId(),BigInteger.ONE,selected.operation(),REF,REF,"fixture",BASE,original.deadline());
            var effect=new ActionState.EffectObservation(original.before(),original.source(),original.sessionId(),selected.expected().observerSchema(),selected.expected().values(),
                    new ObservationProvenance.Query("focus-read"),BASE.plusMillis(1),REF);
            return new ActionReceipt(1,1,selected,ActionCodec.bodySha256(selected),new ActionState.CompositeSettled(
                    new CompositeExecution("fixture-focus/v1",BASE,guard,List.of()),new ActionState.Applied(effect)));
        }
        private org.xar.ck3.control.application.planning.OrdinaryPlanCompletion.Published publication() {
            var row=org.xar.ck3.control.contracts.StrictJson.object();row.put("schema","root.ck3.continuity-window/v1");row.put("machine_id",SESSION.machineId());
            row.put("sequence",0);row.put("window_id",1);row.put("status","running");row.put("start_date_raw",24000);row.put("target_date_raw",286992);
            row.put("target_days",10958);row.put("last_settled_cycles",0);row.put("last_settled_date_raw",24000);row.put("binding_lineage_count",0);
            var before=org.xar.ck3.control.continuity.ContinuityState.fromJson(row,SESSION.machineId());row.put("sequence",1);
            var after=org.xar.ck3.control.continuity.ContinuityState.fromJson(row,SESSION.machineId());
            var head=new org.xar.ck3.control.continuity.writer.WriterContracts.Head(before,List.of(),List.of(),List.of(),false);
            var receipt=new org.xar.ck3.control.continuity.writer.WriterContracts.Receipt(org.xar.ck3.control.continuity.writer.WriterContracts.Disposition.COMMITTED,after,"a".repeat(64),1,false);
            return new org.xar.ck3.control.application.planning.OrdinaryPlanCompletion.Published(head,receipt);
        }
        SessionController controller() {
            CheckpointFiles files = new CheckpointFiles() {
                @Override public Optional<CheckpointPair.FileWitness> observe(Path path) { throw new AssertionError("unexpected SAVE file observation"); }
                @Override public byte[] read(CheckpointPair.FileWitness witness, int maximum) { throw new AssertionError("unexpected SAVE read"); }
                @Override public CheckpointPair.FileWitness replace(Path path, byte[] bytes) { throw new AssertionError("unexpected SAVE write"); }
                @Override public CheckpointPair.FileWitness createNew(Path path, byte[] bytes) { throw new AssertionError("unexpected SAVE creation"); }
                @Override public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness source, Path target) { throw new AssertionError("unexpected SAVE copy"); }
            };
            DriverCheckpointStore.SnapshotSupplier snapshot = new DriverCheckpointStore.SnapshotSupplier() {
                @Override public <T> T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) throws IOException { return work.run(new DriverStateSnapshot.Incomplete(List.of("fixture never saves")), (a,b) -> { throw new AssertionError("unexpected checkpoint publication"); }); }
            };
            var drivers = new DriverCheckpointStore(files, Path.of("D:/fixture/Driver.json"), "fixture-pipe", snapshot);
            CheckpointRequest.ObservationPort readiness = until -> { throw new AssertionError("unexpected SAVE readiness"); };
            var service = new CheckpointService(files, drivers, readiness, Path.of("D:/fixture/evidence"), Clock.fixed(BASE, ZoneOffset.UTC),
                    (pair,receipt) -> { throw new AssertionError("unexpected first-seed adoption"); });
            var factory = new CheckpointRequestFactory(Path.of("D:/fixture/xar_checkpoint.ck3"), readiness);
            RealmLifecycle realm = new RealmLifecycle(REF);
            List<OrdinaryPolicy> policies = completePlanner ? Arrays.stream(PlanningStage.values()).<OrdinaryPolicy>map(stage -> {
                if (stage == PlanningStage.REALM_MEMBERSHIP_PUBLICATION) return realm;
                return new OrdinaryPolicy() {
                @Override public PlanningStage stage() { return stage; }
                @Override public ExactRef implementationSource() { return REF; }
                @Override public Decision evaluate(PlanningRequest input, Draft previous) {
                    if (stage != PlanningStage.ORDINARY_CORE) return new Keep("test preserves preceding plan");
                    time.waitFor(planningDelay);
                    if (reconcileExisting) return new ReconcileExisting("original-action", new OpportunityJson.Obj(Map.of()), "read original pending action only");
                    return new Replace(new Draft("fixture", "fixture", "fixture", Kind.ORDINARY, Optional.of(command(input)), Purpose.WORLD_ACTION, Optional.empty(), new OpportunityJson.Obj(Map.of())), "fixture actual action selection");
                }
                };
            }).toList() : List.of();
            var planner = new OrdinaryPlanner(policies, Clock.fixed(BASE, ZoneOffset.UTC), realm);
            ActionCoordinatorPort actions = new ActionCoordinatorPort() {
                @Override public CompositeContinuationReport continueOriginalComposite(CompositeContinuationToken token)throws IOException {
                    assertEquals(0,scopeDepth);
                    if(continuationProvider.isEmpty())return ActionCoordinatorPort.super.continueOriginalComposite(token);
                    continuationCalls++;return continuationProvider.orElseThrow().apply(token);
                }
                @Override public ActionReceipt execute(ActionCommand command) {
                    if(readRefreshBeforeDispatch&&!readRefreshIssued){readRefreshIssued=true;if(refreshHasParent)readParentOriginal=command;throw new ReadPublicationRefreshException(command,Optional.empty(),publication(),refreshHasParent?Optional.of(command.actionId()):Optional.empty());}
                    submitted.incrementAndGet(); return new ActionReceipt(1, 1, command, ActionCodec.bodySha256(command),
                            new ActionState.Unknown(Optional.empty(), Optional.empty(), "original completion lost", List.of(REF)));
                }
                @Override public ActionReceipt reconcile(String id) {
                    if (!reconcileExisting&&!refreshHasParent) throw new AssertionError("ordinary loop must not automatically reconcile UNKNOWN as a new turn");
                    reconciled.incrementAndGet(); var original = readParentOriginal!=null?readParentOriginal:terminalOriginal!=null?terminalOriginal:command(request(BASE.plusSeconds(1)), id);
                    return new ActionReceipt(1, 1, original, ActionCodec.bodySha256(original), new ActionState.Unknown(Optional.empty(), Optional.empty(), "original completion remains unknown", List.of(REF)));
                }
            };
            var saveRef = new ExactRef("D:/fixture/xar_checkpoint.ck3", 1, "b".repeat(64));
            var driverRef = new ExactRef("D:/fixture/Driver.json", 1, "c".repeat(64));
            var baseline = new CheckpointPair(new CheckpointPair.FileWitness(saveRef, new FileStatIdentity(BigInteger.ONE, "9007199254740993", "134000000000000001")),
                    new CheckpointPair.FileWitness(driverRef, new FileStatIdentity(BigInteger.ONE, "9007199254740995", "134000000000000003")), request(BASE.plusSeconds(5)).before(), "lineage-1", 1, "save-initial", REF, BASE);
            EpisodeContinuation episodes=(owner,receipt,after)->{episodeCalls++;throw new IOException("fixture has no live committed private lifecycle producer");};
            ObservationPort actualObserver=new ObservationPort() {
                @Override public Observation observe(SessionIdentity expected,Instant until)throws IOException,InterruptedException{return observer.observe(expected,until);}
                @Override public Optional<PendingSuccessorUi> pendingSuccessorUi(SessionIdentity expected,Instant until){assertEquals(0,scopeDepth);return pendingProbe.apply(expected,until);}
            };
            var controller = new SessionController(SESSION, life, actualObserver, planner, actions, service, factory, writer, analysis, time, withBaseline ? Optional.of(baseline) : Optional.empty(), 0,completion,episodes);
            if (bindRetainedSource) controller.bindRetainedIncidents(retainedSource);
            return controller;
        }
    }
    private static SemanticEvidence semantic(PlanningRequest request) {
        return new SemanticEvidence(request.before(), new ExactRef("D:/fixture/semantic.json", 1, "e".repeat(64)), REF,
                new ExactRef("D:/fixture/driver-stamp.json", 1, "f".repeat(64)), new ExactRef("D:/fixture/Driver.json", 1, "c".repeat(64)), BASE);
    }
}
