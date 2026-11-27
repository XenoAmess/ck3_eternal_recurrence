package org.xar.ck3.control.application.session;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
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
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.contracts.offline.OfflineEventAnalysisContract.BatchRequest;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Public Controller DATA seams. A SAVE admission probe stops before any physical checkpoint or Game operation. */
final class SessionControllerAnnualSaveTest {
    private static final Instant BASE = Instant.parse("2026-11-04T00:00:00Z");
    private static final long SAVED_DATE = 53_154_744L;
    private static final ExactRef REF = new ExactRef("D:/annual-fixture/native.json", 1, "a".repeat(64));
    private static final GameGeneration GAME = new GameGeneration(123,
            new PythonOnlyUInt64(new BigInteger("134000000000000001")));
    private static final SessionIdentity OWNER = new SessionIdentity("annual-fixture", GAME, "annual-session");

    @Test void dirtyStateAndSavedDateSurviveBatchesUntilTheExactYearInsteadOfLifeCount() {
        Fixture f = new Fixture(true); SessionController controller = f.controller();
        f.advanceRaw = 364L * 24;
        BatchReport first = controller.runBatch(limits("year-before", 1));
        assertEquals(BatchReport.Terminal.TURN_BOUND, first.terminal(), first::detail);
        assertTrue(first.dirtySinceSave()); assertEquals(1, first.eligibleAdvancesSinceSave());
        assertEquals(0, f.saveAdmissions); assertEquals(1, f.actions);
        f.advanceRaw = 0;
        BatchReport second = controller.runBatch(limits("year-another-life", 1));
        assertEquals(BatchReport.Terminal.TURN_BOUND, second.terminal(), second::detail);
        assertEquals(2, f.actions); assertEquals(0, f.saveAdmissions);
        assertEquals(f.baseline, second.lastSavedPair().orElseThrow());
        f.dateRaw = SAVED_DATE + 365L * 24;
        BatchReport due = controller.runBatch(limits("year-exact", 100_000));
        assertSaveAdmission(due, f, 2);
        assertEquals(f.baseline, controller.savedPair().orElseThrow());
        assertEquals(0, due.committedSavedDays(), "admission is not a confirmed SAVE");
    }

    @Test void underYearTailUsesItsOwnFrameForTheReportAndBatchFinish() {
        Fixture f = new Fixture(true);
        f.narrowTail = true;
        f.tailRevisionChange = true;
        var progressedIncident = new BatchRequest("tail-progress-incident", REF, List.of(REF));
        f.tailAnalysis = Optional.of(progressedIncident);
        SessionController controller = f.controller();

        var report = controller.runBatch(limits("under-year-tail", 1));

        assertEquals(BatchReport.Terminal.TURN_BOUND, report.terminal(), report::detail);
        assertEquals(2, f.fullObservations, "ordinary plan and post-RETAIN still use full Ready");
        assertEquals(1, f.tailObservations);
        assertEquals(0, f.saveAdmissions);
        assertTrue(report.dirtySinceSave());
        assertEquals(1, report.eligibleAdvancesSinceSave());
        assertEquals(f.baseline, report.lastSavedPair().orElseThrow());
        var frame = f.request(BASE.plusSeconds(10)).before();
        var boundary = controller.lastBatchBoundary().orElseThrow();
        assertEquals(3, boundary.observationCount());
        assertEquals(frame, boundary.lastObservation().orElseThrow());
        assertEquals(JournalKind.BATCH_FINISHED, f.journal.getLast().kind());
        assertEquals(frame, f.journal.getLast().frame().orElseThrow());
        assertEquals(List.of(progressedIncident), f.queuedAnalyses);
        assertEquals(List.of(progressedIncident.batchId()), report.pendingAnalysisBatchIds());
    }

    @Test void sameSessionNameCannotAdmitAnotherGameAndItsPhysicalBaseline() {
        var predecessor = new GameGeneration(122, GAME.creationFiletime());
        Fixture f = new Fixture(true, predecessor);
        f.foreignTail = true;
        SessionController controller = f.controller();

        var report = controller.runBatch(limits("wrong-owner-tail", 1));

        assertEquals(BatchReport.Terminal.INTERNAL_FAILURE, report.terminal(), report::detail);
        assertTrue(report.detail().contains("requires its original owned Game"), report::detail);
        assertEquals(1, f.tailObservations);
        assertEquals(0, f.saveAdmissions);
        assertEquals(GAME, controller.lastBatchBoundary().orElseThrow().lastObservation().orElseThrow().game());
        assertEquals(f.baseline, report.lastSavedPair().orElseThrow());
    }

    @Test void currentTailCrossesTheYearAfterAnUnderYearAfterCycle() {
        Fixture f = new Fixture(true);
        f.advanceRaw = 8759;
        f.narrowTail = true;
        f.tailRawAdjustment = 1;

        var report = f.controller().runBatch(limits("tail-just-crossed-year", 1));

        assertSaveAdmission(report, f, 1);
        assertEquals(1, f.tailObservations);
        assertEquals(3, f.fullObservations);
        assertEquals(f.baseline, report.lastSavedPair().orElseThrow());
    }

    @Test void terminalTailIsDeferredWithoutUsingThePriorOrdinaryFrameAsSaveAuthority() {
        Fixture f = new Fixture(true);
        f.terminalAtTail = true;
        SessionController controller = f.controller();

        var report = controller.runBatch(limits("terminal-during-tail", 1));

        assertEquals(BatchReport.Terminal.CHECKPOINT_DEFERRED, report.terminal(), report::detail);
        assertEquals(2, f.fullObservations);
        assertEquals(1, f.tailObservations);
        assertEquals(0, f.saveAdmissions);
        assertTrue(report.dirtySinceSave());
        assertTrue(report.lastTerminalObservation().isPresent());
        assertEquals(JournalKind.BATCH_DEFERRED, f.journal.getLast().kind());
        assertTrue(f.journal.getLast().frame().isEmpty());
        assertEquals(f.baseline, report.lastSavedPair().orElseThrow());
    }

    @Test void exactYearAndOvershootAreAlsoCheckedAtTheOrdinaryDirtyBatchTail() {
        for (long days : List.of(365L, 366L)) {
            Fixture f = new Fixture(true); f.advanceRaw = days * 24;
            BatchReport report = f.controller().runBatch(limits("tail-" + days, 100_000));
            assertSaveAdmission(report, f, 1);
            assertTrue(report.dirtySinceSave());
            assertEquals(f.baseline, report.lastSavedPair().orElseThrow());
        }
    }

    @Test void operatorStopCannotForceAnEarlyDirtyTailSave() {
        Fixture f = new Fixture(true); f.advanceRaw = 10 * 24;
        SessionController controller = f.controller();
        assertEquals(BatchReport.Terminal.TURN_BOUND, controller.runBatch(limits("before-stop", 1)).terminal());
        controller.requestStop();
        BatchReport stopped = controller.runBatch(limits("stop-under-year", 1));
        assertEquals(BatchReport.Terminal.OPERATOR_STOP, stopped.terminal(), stopped::detail);
        assertTrue(stopped.dirtySinceSave()); assertEquals(1, f.actions); assertEquals(0, f.saveAdmissions);
        assertEquals(f.baseline, stopped.lastSavedPair().orElseThrow());
    }

    @Test void operatorStopEnteringReadinessUsesTheAnnualTailAt8759And8760Ticks() {
        Fixture f = new Fixture(true); f.advanceRaw = 8759; f.narrowTail = true;
        SessionController controller = f.controller();
        assertEquals(BatchReport.Terminal.TURN_BOUND, controller.runBatch(limits("before-stop-8759", 1)).terminal());

        f.beforeNextPlanningScope = controller::requestStop;
        var underYear = controller.runBatch(limits("stopped-at-8759", 1));
        assertEquals(BatchReport.Terminal.OPERATOR_STOP, underYear.terminal(), underYear::detail);
        assertEquals(2, f.tailObservations);
        assertEquals(0, f.saveAdmissions);
        assertTrue(underYear.dirtySinceSave());
        assertEquals(f.baseline, underYear.lastSavedPair().orElseThrow());

        controller.resume();
        f.dateRaw++; f.revision++;
        f.beforeNextPlanningScope = controller::requestStop;
        var due = controller.runBatch(limits("stopped-at-8760", 1));
        assertSaveAdmission(due, f, 1);
        assertEquals(3, f.tailObservations);
        assertTrue(due.dirtySinceSave());
        assertEquals(f.baseline, due.lastSavedPair().orElseThrow());
        assertEquals(0, due.committedSavedDays());
    }

    @Test void operatorStopEnteringReadinessStillRequiresASafeAnnualTail() {
        Fixture f = new Fixture(true); f.advanceRaw = 8759;
        SessionController controller = f.controller();
        assertEquals(BatchReport.Terminal.TURN_BOUND, controller.runBatch(limits("before-modal-stop", 1)).terminal());

        f.dateRaw++; f.revision++;
        f.eligibility = CheckpointEligibility.MODAL_PENDING;
        f.beforeNextPlanningScope = controller::requestStop;
        var blocked = controller.runBatch(limits("stopped-with-modal", 1));
        assertEquals(BatchReport.Terminal.CHECKPOINT_DEFERRED, blocked.terminal(), blocked::detail);
        assertEquals(2, f.tailObservations);
        assertEquals(0, f.saveAdmissions);
        assertEquals(1, f.actions);
        assertTrue(blocked.dirtySinceSave());
        assertEquals(f.baseline, blocked.lastSavedPair().orElseThrow());
    }

    @Test void operatorStopDuringPostActionReadinessStillSettlesTheIssuedCycle() {
        Fixture f = new Fixture(true); f.narrowTail = true;
        SessionController controller = f.controller();
        f.afterAction = () -> f.beforeNextPlanningScope = controller::requestStop;

        var report = controller.runBatch(new BatchLimits("stopped-after-action", 2,
                Duration.ofSeconds(30), Duration.ofSeconds(1), Duration.ofMillis(1), 1));

        assertEquals(BatchReport.Terminal.OPERATOR_STOP, report.terminal(), report::detail);
        assertEquals(1, f.actions);
        assertEquals(1, f.settledCycles);
        assertEquals(1, f.tailObservations);
        assertEquals(0, f.saveAdmissions);
        assertTrue(report.dirtySinceSave());
        assertEquals(f.baseline, report.lastSavedPair().orElseThrow());
        assertEquals(JournalKind.BATCH_FINISHED, f.journal.getLast().kind());
    }

    @Test void yearlySaveStillRequiresSafeReadinessAndRetainsDirtyStateWhileBlocked() {
        Fixture f = new Fixture(true); f.advanceRaw = 365 * 24; f.afterEligibility = CheckpointEligibility.MODAL_PENDING;
        SessionController controller = f.controller();
        BatchReport blocked = controller.runBatch(limits("year-modal", 1));
        assertEquals(BatchReport.Terminal.CHECKPOINT_DEFERRED, blocked.terminal(), blocked::detail);
        assertTrue(blocked.dirtySinceSave()); assertEquals(0, f.saveAdmissions);
        f.eligibility = CheckpointEligibility.SAFE;
        assertSaveAdmission(controller.runBatch(limits("year-safe-again", 1)), f, 1);
    }

    @Test void missingPhysicalBaselineCanInitializeWithoutWaitingForAYear() {
        Fixture f = new Fixture(false); f.advanceRaw = 24;
        BatchReport first = f.controller().runBatch(limits("initial-baseline", 1));
        assertSaveAdmission(first, f, 1);
        assertTrue(first.lastSavedPair().isEmpty()); assertEquals(0, first.committedSavedDays());
    }

    @Test void anOriginalUnknownNeverTurnsIntoAnotherActionOrSaveInTheNextBatch() {
        Fixture f = new Fixture(true); f.unknown = true;
        SessionController controller = f.controller();
        BatchReport original = controller.runBatch(limits("unknown-original", 1));
        assertEquals(BatchReport.Terminal.ACTION_UNKNOWN, original.terminal(), original::detail);
        f.dateRaw = SAVED_DATE + 400L * 24;
        BatchReport following = controller.runBatch(limits("unknown-following", 1));
        assertEquals(BatchReport.Terminal.INTERNAL_FAILURE, following.terminal());
        assertTrue(controller.isQuarantined()); assertEquals(1, f.actions); assertEquals(0, f.saveAdmissions);
        assertEquals(f.baseline, following.lastSavedPair().orElseThrow());
    }

    private static void assertSaveAdmission(BatchReport report, Fixture f, int actions) {
        assertEquals(1, f.saveAdmissions, report::detail);
        assertEquals(actions, f.actions, "annual gate must run before another gameplay submission");
        assertEquals(BatchReport.Terminal.INTERNAL_FAILURE, report.terminal());
        assertTrue(report.detail().contains("annual SAVE admission probe"), report::detail);
        assertTrue(f.journal.stream().noneMatch(row -> row.kind() == JournalKind.SAVE_CONFIRMED));
    }
    private static BatchLimits limits(String id, int legacyCount) {
        return new BatchLimits(id, 1, Duration.ofSeconds(30), Duration.ofSeconds(1), Duration.ofMillis(1), legacyCount);
    }
    private static final class TestClock implements SessionClock {
        long nanos;
        @Override public Tick now() { return new Tick(nanos, BASE.plusNanos(nanos++)); }
        @Override public void waitFor(Duration duration) { nanos += duration.toNanos(); }
    }
    private static final class Fixture {
        final TestClock clock = new TestClock();
        final List<JournalInput> journal = new ArrayList<>();
        final boolean withBaseline;
        final CheckpointPair baseline;
        long dateRaw = SAVED_DATE, advanceRaw = 24, revision = 1;
        int actions, saveAdmissions, fullObservations, tailObservations, tailRawAdjustment, settledCycles;
        boolean narrowTail, tailRevisionChange, terminalAtTail, foreignTail;
        Runnable beforeNextPlanningScope = () -> { };
        Runnable afterAction = () -> { };
        Optional<BatchRequest> tailAnalysis = Optional.empty();
        final List<BatchRequest> queuedAnalyses = new ArrayList<>();
        boolean unknown;
        CheckpointEligibility eligibility = CheckpointEligibility.SAFE, afterEligibility = CheckpointEligibility.SAFE;
        Fixture(boolean withBaseline) {
            this(withBaseline, GAME);
        }
        Fixture(boolean withBaseline, GameGeneration savedGame) {
            this.withBaseline = withBaseline;
            var save = new ExactRef("D:/annual-fixture/save.ck3", 1, "b".repeat(64));
            var driver = new ExactRef("D:/annual-fixture/Driver.json", 1, "c".repeat(64));
            baseline = new CheckpointPair(new CheckpointPair.FileWitness(save,
                    new FileStatIdentity(BigInteger.ONE, "9007199254740993", "134000000000000001")),
                    new CheckpointPair.FileWitness(driver,
                    new FileStatIdentity(BigInteger.ONE, "9007199254740995", "134000000000000003")),
                    new ObservationIdentity(OWNER.machineId(), savedGame, request(BASE.plusSeconds(10)).before().frame(), 1),
                    "annual-lineage", 1, "saved-original", REF, BASE);
        }
        PlanningRequest request(Instant deadline) {
            var before = new ObservationIdentity(OWNER.machineId(), GAME,
                    new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),
                    BigInteger.valueOf(revision), BigInteger.valueOf(dateRaw)), "annual-" + revision,
                    BigInteger.valueOf(revision), "annual-episode"), 1);
            String json = "{\"paused\":true,\"map_ready\":true,\"revision\":" + revision
                    + ",\"native_revision\":" + revision + ",\"date_raw\":" + dateRaw
                    + ",\"snapshot_id\":\"annual-" + revision + "\",\"episode_run_id\":\"annual-episode\","
                    + "\"played_character\":{\"character_id\":29829},\"active_wars\":[],\"player_armies\":[]}";
            var observation = new PlanningObservation(OpportunityJson.object(OpportunityJson.parse(json.getBytes(StandardCharsets.UTF_8)), "annual fixture"),
                    List.of(), Set.of(new OperationKey("annual-fixture-action")), Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false);
            return new PlanningRequest(before, new G2Source(OWNER.machineId(), BASE.toString(), "annual-fixture", REF), OWNER.sessionId(), deadline, observation);
        }
        SemanticEvidence semantic(PlanningRequest request) {
            return new SemanticEvidence(request.before(), new ExactRef("D:/annual-fixture/semantic.json", 1, "d".repeat(64)), REF,
                    new ExactRef("D:/annual-fixture/stamp.json", 1, "e".repeat(64)), baseline.driver().reference(), BASE);
        }
        ActionCommand command(PlanningRequest request) {
            return new ActionCommand("annual-action-" + (actions + 1), request.before(), request.source(), OWNER.sessionId(),
                    new OperationKey("annual-fixture-action"), new OpportunityJson.Obj(Map.of()),
                    new ExpectedPostcondition(1, request.before(), request.source(), "annual-effect/v1",
                    List.of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true))),
                    new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), request.deadline());
        }
        SessionController controller() {
            CheckpointFiles files = new CheckpointFiles() {
                @Override public Optional<CheckpointPair.FileWitness> observe(Path path) { throw unused(); }
                @Override public byte[] read(CheckpointPair.FileWitness witness, int maximum) { throw unused(); }
                @Override public CheckpointPair.FileWitness replace(Path path, byte[] bytes) { throw unused(); }
                @Override public CheckpointPair.FileWitness createNew(Path path, byte[] bytes) { throw unused(); }
                @Override public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness source, Path target) { throw unused(); }
            };
            DriverCheckpointStore.SnapshotSupplier snapshots = new DriverCheckpointStore.SnapshotSupplier() {
                @Override public <T> T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) { throw unused(); }
            };
            var drivers = new DriverCheckpointStore(files, Path.of("D:/annual-fixture/Driver.json"), "annual-fixture", snapshots);
            CheckpointRequest.ObservationPort saveProbe = until -> {
                saveAdmissions++; throw new IllegalStateException("annual SAVE admission probe; physical SAVE is deliberately unavailable");
            };
            var checkpoints = new CheckpointService(files, drivers, saveProbe, Path.of("D:/annual-fixture/evidence"),
                    Clock.fixed(BASE, ZoneOffset.UTC), (pair, receipt) -> { throw unused(); });
            var requests = new CheckpointRequestFactory(Path.of("D:/annual-fixture/save.ck3"), saveProbe);
            RealmLifecycle realm = new RealmLifecycle(REF);
            List<OrdinaryPolicy> policies = Arrays.stream(PlanningStage.values()).<OrdinaryPolicy>map(stage -> {
                if (stage == PlanningStage.REALM_MEMBERSHIP_PUBLICATION) return realm;
                return new OrdinaryPolicy() {
                    @Override public PlanningStage stage() { return stage; }
                    @Override public ExactRef implementationSource() { return REF; }
                    @Override public Decision evaluate(PlanningRequest request, Draft previous) {
                        return stage == PlanningStage.ORDINARY_CORE
                                ? new Replace(new Draft("annual", "annual", "annual", Kind.ORDINARY, Optional.of(command(request)),
                                Purpose.WORLD_ACTION, Optional.empty(), new OpportunityJson.Obj(Map.of())), "annual fixture action")
                                : new Keep("preserve previous plan");
                    }
                };
            }).toList();
            var planner = new OrdinaryPlanner(policies, Clock.fixed(BASE, ZoneOffset.UTC), realm);
            ActionCoordinatorPort actionPort = new ActionCoordinatorPort() {
                @Override public ActionReceipt execute(ActionCommand command) {
                    actions++;
                    if (unknown) return new ActionReceipt(1, actions, command, ActionCodec.bodySha256(command),
                            new ActionState.Unknown(Optional.empty(), Optional.empty(), "original unknown", List.of(REF)));
                    dateRaw += advanceRaw; revision++; eligibility = afterEligibility;
                    var after = request(command.deadline());
                    var flags = List.<ExpectedValue>of(new ExpectedBoolean(new FieldKey("native.gameplay_verified"), true),
                            new ExpectedBoolean(new FieldKey("timeline.advance_verified"), true),
                            new ExpectedBoolean(new FieldKey("timeline.checkpoint_eligible"), true),
                            new ExpectedText(new FieldKey("progress_status"), "postcondition"));
                    var guard = new GuardEvidence(command.before(), command.source(), OWNER.sessionId(), BigInteger.ONE,
                            command.operation(), REF, REF, "annual", BASE, command.deadline());
                    var effect = new ActionState.EffectObservation(after.before(), after.source(), OWNER.sessionId(),
                            command.expected().observerSchema(), flags, new ObservationProvenance.Query("annual-after"), BASE.plusMillis(1), REF);
                    return new ActionReceipt(1, actions, command, ActionCodec.bodySha256(command),
                            new ActionState.CompositeSettled(new CompositeExecution("annual-fixture/v1", BASE, guard, List.of()), new ActionState.Applied(effect)));
                }
                @Override public ActionReceipt reconcile(String id) { throw unused(); }
            };
            BatchJournal writer = new BatchJournal() {
                @Override public JournalCommit commit(JournalInput row) { journal.add(row); return new JournalCommit(REF, 0); }
                @Override public void validateOrdinarySubmission(SessionIdentity owner, SemanticEvidence evidence) { assertEquals(OWNER, owner); }
                @Override public Optional<CompletedCycleProof> cycleProof(SessionIdentity owner, SemanticEvidence evidence) {
                    return Optional.of(new CompletedCycleProof(actions, evidence, "f".repeat(64)));
                }
                @Override public void retainCycle(SessionIdentity owner, ActionReceipt receipt) { assertTrue(receipt.settled()); }
                @Override public boolean requiresFreshAfterCycle(SessionIdentity owner, ActionReceipt receipt) { return true; }
                @Override public CompletedCycleProof settleCycle(SessionIdentity owner, ActionReceipt receipt, SemanticEvidence evidence) {
                    assertEquals(receipt.applied().orElseThrow().observation().after(), evidence.frame());
                    settledCycles++;
                    return new CompletedCycleProof(actions, evidence, "f".repeat(64));
                }
            };
            OrdinaryPlanCompletion.PlanningScope scope = new OrdinaryPlanCompletion.PlanningScope() {
                @Override public <T> ScopeResult<T> inPlanningScope(ScopeWork<T> work) throws IOException, InterruptedException {
                    var beforeScope = beforeNextPlanningScope;
                    beforeNextPlanningScope = () -> { };
                    beforeScope.run();
                    return new ScopeResult<>(work.run(), Optional.empty());
                }
                @Override public PlanningDisposition afterPlanning(PlanningRequest request, PlanningResult planned) { return new Unchanged("annual DATA fixture"); }
                @Override public ExecutionDisposition afterExecution(ActionReceipt receipt) {
                    afterAction.run();
                    return new Unchanged("annual DATA fixture");
                }
            };
            ObservationPort observer = new ObservationPort() {
                @Override public Observation observe(SessionIdentity owner, Instant until) {
                    fullObservations++;
                    var request = request(until);
                    return new Ready(request, eligibility, Optional.empty(), Optional.of(semantic(request)));
                }
                @Override public Observation observeCheckpointTail(SessionIdentity owner, ObservationIdentity lastSaved,
                        Instant readinessDeadline, Instant planningDeadline) {
                    tailObservations++;
                    if (terminalAtTail) {
                        var actual = new LifecycleIdentity(OWNER.machineId(), GAME, OWNER.sessionId(), BigInteger.ONE,
                                new LifecycleIdentity.Subject(BigInteger.valueOf(29829), "annual-episode", 1, 2),
                                new LifecycleIdentity.Frame("terminal-tail", BigInteger.valueOf(revision + 1),
                                        BigInteger.valueOf(revision + 1), BigInteger.valueOf(dateRaw), true, false),
                                new LifecycleIdentity.Null(), LifecycleIdentity.TerminalReason.MISSING,
                                new LifecycleIdentity.Evidence(REF, baseline.save().reference(), baseline.driver().reference(),
                                        new ExactRef("D:/annual-fixture/original-driver.json", 1, "d".repeat(64)),
                                        new ExactRef("D:/annual-fixture/source-proof.json", 1, "e".repeat(64))), BASE);
                        return new TerminalReady(actual, new TerminalWait("actual terminal needs its own decision"));
                    }
                    if (tailRevisionChange) revision++;
                    dateRaw += tailRawAdjustment;
                    var request = request(planningDeadline);
                    var captured = semantic(request);
                    if (foreignTail) {
                        var predecessorFrame = new ObservationIdentity(owner.machineId(), lastSaved.game(), captured.frame().frame(), 1);
                        assertTrue(belowAnnualSave(lastSaved, predecessorFrame), "the foreign pair alone is internally consistent");
                        return new CheckpointTailNotDue(new SemanticEvidence(predecessorFrame, captured.semantic(), captured.originalNativePacket(),
                                captured.driverStamp(), captured.originalDriver(), captured.observedAt()), owner.sessionId(), Optional.empty());
                    }
                    return narrowTail && eligibility == CheckpointEligibility.SAFE && belowAnnualSave(lastSaved, request.before())
                            ? new CheckpointTailNotDue(captured, OWNER.sessionId(), tailAnalysis) : observe(owner, planningDeadline);
                }
            };
            var controller = new SessionController(OWNER, (owner, until) -> new GameLifecycle.Running(GAME, REF), observer,
                    planner, actionPort, checkpoints, requests, writer, work -> {
                        assertEquals(tailAnalysis.orElseThrow(), work);
                        queuedAnalyses.add(work);
                        return new AnalysisTicket(work.batchId(), new CompletableFuture<>());
                    }, clock,
                    withBaseline ? Optional.of(baseline) : Optional.empty(), 0, scope, (owner, receipt, until) -> { throw unused(); });
            controller.bindRetainedIncidents(List::of);
            return controller;
        }
        private static AssertionError unused() { return new AssertionError("fixture must not perform physical SAVE, Game or unrelated work"); }
    }
}
