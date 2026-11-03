package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Real software Controller/Loop calls. The opt-in callback tests scheduling only, never a Root capture issuer.
 * The real private Controller predicate is invoked reflectively; actual capture must still reject this RAM journal.
 * No Root/physical SAVE/canonical writer/Native permission or full capture lifecycle is claimed.
 */
final class WarmPlanningRetry369BTest {
    private static final Instant BASE = Instant.parse("2026-11-03T00:00:00Z");
    private static final Duration WALL = Duration.ofSeconds(300);
    private static final BigInteger DATE = BigInteger.valueOf(53144328);
    private static final ExactRef REF = new ExactRef("D:/software-data-not-opened/warm-source", 1, "a".repeat(64));
    private static final GameGeneration GAME = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
    private static final SessionIdentity OWNER = new SessionIdentity("software-warm", GAME, "software-warm-session");
    private enum Mode { GENERIC, BUDGET, SOURCE_STOP, MIGRATION_STOP, COMPLETION_BLOCKED, AWAITING }

    @Test void oneAllowanceIsSharedAcrossGenericWallsAndLifeBudgetYields() throws Exception {
        for (var modes : List.of(List.of(Mode.GENERIC, Mode.GENERIC),
                List.of(Mode.GENERIC, Mode.BUDGET), List.of(Mode.BUDGET, Mode.GENERIC))) {
            var fixture = new Fixture(modes, List.of(DATE, DATE), true, false, false);
            var controller = fixture.controller();
            var result = run(fixture, controller, null, false, false);
            assertEquals(RootOrdinaryWorkerLoop.StopReason.NO_PROGRESS, result.stopReason(), result.toString());
            assertEquals(2, fixture.completed.size(), "one fresh batch, even when the two no-dispatch reasons differ");
            assertEquals(2, result.nextBatchSequence());
            assertEquals(0, fixture.actions);
            assertNotEquals(fixture.completed.getFirst().committedLedgerHead(), fixture.completed.getLast().committedLedgerHead());
            assertNotEquals(fixture.completed.getFirst().lastPlan().orElseThrow().before().frame().revision(),
                    fixture.completed.getLast().lastPlan().orElseThrow().before().frame().revision());
            for (var report : fixture.completed) {
                assertEquals(BatchReport.Terminal.WALL_TIMEOUT, report.terminal());
                assertEquals(0, report.committedSavedDays());
                assertTrue(report.turns().isEmpty());
                assertFalse(report.dirtySinceSave());
            }
            assertFalse(qualifies(controller, fixture.completed.getFirst()), "old actual reports are not current qualifications");
        }
    }

    @Test void onlyAnActualForwardDateResetsTheSingleWarmOpportunity() throws Exception {
        var forward = new Fixture(List.of(Mode.GENERIC), List.of(DATE, DATE.add(BigInteger.valueOf(24)),
                DATE.add(BigInteger.valueOf(24)), DATE.add(BigInteger.valueOf(24))), true, false, false);
        var result = run(forward, forward.controller(), null, false, false);
        assertEquals(RootOrdinaryWorkerLoop.StopReason.NO_PROGRESS, result.stopReason());
        assertEquals(4, forward.completed.size(), "forward observed date permits a new single opportunity, not endless warm continuation");
        assertEquals(0, forward.actions);
        assertTrue(forward.completed.stream().allMatch(report -> report.committedSavedDays() == 0), "observed software dates are not SAVE credit");

        var rollback = new Fixture(List.of(Mode.GENERIC), List.of(DATE, DATE.subtract(BigInteger.valueOf(24)), DATE, DATE), true, false, false);
        var stopped = run(rollback, rollback.controller(), null, false, false);
        assertEquals(RootOrdinaryWorkerLoop.StopReason.NO_PROGRESS, stopped.stopReason());
        assertEquals(4, rollback.completed.size(), "returning to the original date does not reset the used opportunity");
        assertEquals(0, rollback.actions);
    }

    @Test void actualQualificationsAndOriginalFailuresCannotBeManufacturedOrBypassed() throws Exception {
        var fixture = new Fixture(List.of(Mode.GENERIC), List.of(DATE), true, false, false);
        var controller = fixture.controller();
        var actual = controller.runBatch(limits("warm-software-0"));
        assertTrue(qualifies(controller, actual));
        assertFalse(qualifies(controller, copy(actual)), "equal public DATA is not an actual producer qualification");
        assertSame(actual, controller.runBatch(limits("warm-software-0")), "cached report does not execute again");
        assertTrue(qualifies(controller, actual));
        assertEquals(1, fixture.observations);

        var absent = new Fixture(List.of(Mode.GENERIC), List.of(DATE), false, false, false);
        var noBaseline = run(absent, absent.controller(), null, false, false);
        assertEquals(RootOrdinaryWorkerLoop.StopReason.NO_PROGRESS, noBaseline.stopReason());
        assertEquals(1, absent.completed.size());
        var pending = new Fixture(List.of(Mode.GENERIC), List.of(DATE), true, true, false);
        var pendingController = pending.controller();
        var pendingReport = pendingController.runBatch(limits("warm-software-0"));
        assertTrue(pendingController.lastBatchBoundary().orElseThrow().pendingAction());
        assertFalse(qualifies(pendingController, pendingReport));

        // The new B profile intentionally qualifies generic pre-completion walls via actual capture,
        // rather than inventing a safe PlanningDisposition that was never returned.
        assertThrows(ContractViolationException.class, () -> controller.captureCleanPlanningWall(
                null, "warm-software", 1, actual), "pure scheduling facts cannot replace the real canonical capture producer");
        assertFalse(controller.isRunning(), "failed actual capture releases its original CAS");
        assertFalse(qualifies(controller, actual, 2), "the next sequence must follow this actual batch");
        var defaultFixture = new Fixture(List.of(Mode.GENERIC), List.of(DATE), true, false, false);
        var defaultResult = run(defaultFixture, defaultFixture.controller(), null, false, false, false);
        assertEquals(RootOrdinaryWorkerLoop.StopReason.NO_PROGRESS, defaultResult.stopReason());
        assertEquals(1, defaultFixture.completed.size(), "old controls default to no warm opt-in");
        var captureFailure = new IOException("exact software capture failure after callback entry");
        var captureFixture = new Fixture(List.of(Mode.GENERIC), List.of(DATE), true, false, false);
        captureFixture.captureFailure = captureFailure;
        var captureResult = run(captureFixture, captureFixture.controller(), null, false, false);
        assertEquals(RootOrdinaryWorkerLoop.StopReason.CALLBACK_FAILURE, captureResult.stopReason());
        assertEquals(captureFailure.toString(), captureResult.failureDetail().orElseThrow());
        assertEquals(1, captureFixture.captureCalls, "an ambiguous capture callback is never retried");
        assertEquals(1, captureFixture.completed.size());
        var failed = new Fixture(List.of(Mode.GENERIC), List.of(DATE), true, false, true);
        var failedController = failed.controller();
        var failure = run(failed, failedController, null, false, false);
        assertEquals(RootOrdinaryWorkerLoop.StopReason.TERMINAL_FAILURE, failure.stopReason());
        assertEquals(BatchReport.Terminal.WRITER_UNKNOWN, failed.completed.getFirst().terminal());
        assertFalse(qualifies(failedController, failed.completed.getFirst()));
        assertEquals(1, failed.completed.size());

        var callback = new IOException("exact software callback marker");
        var callbackFixture = new Fixture(List.of(Mode.GENERIC), List.of(DATE), true, false, false);
        var callbackResult = run(callbackFixture, callbackFixture.controller(), callback, false, false);
        assertEquals(RootOrdinaryWorkerLoop.StopReason.CALLBACK_FAILURE, callbackResult.stopReason());
        assertEquals(callback.toString(), callbackResult.failureDetail().orElseThrow());
        assertEquals(1, callbackFixture.completed.size());
        var stopFixture = new Fixture(List.of(Mode.GENERIC), List.of(DATE), true, false, false);
        assertEquals(RootOrdinaryWorkerLoop.StopReason.OPERATOR_STOP,
                run(stopFixture, stopFixture.controller(), null, true, false).stopReason());
        assertEquals(1, stopFixture.completed.size());
        boolean interrupted = Thread.interrupted();
        try {
            var interruptFixture = new Fixture(List.of(Mode.GENERIC), List.of(DATE), true, false, false);
            var interruptResult = run(interruptFixture, interruptFixture.controller(), null, false, true);
            assertEquals(RootOrdinaryWorkerLoop.StopReason.CALLBACK_FAILURE, interruptResult.stopReason());
            assertTrue(Thread.currentThread().isInterrupted());
            assertEquals(1, interruptFixture.completed.size());
        } finally { Thread.interrupted(); if (interrupted) Thread.currentThread().interrupt(); }
        assertEquals(0, fixture.actions + absent.actions + pending.actions + failed.actions + callbackFixture.actions + stopFixture.actions);
    }

    private static RootOrdinaryWorkerLoop.Result run(Fixture fixture, SessionController controller,
            IOException callbackFailure, boolean requestStop, boolean interrupt) throws Exception {
        return run(fixture,controller,callbackFailure,requestStop,interrupt,true);
    }
    private static RootOrdinaryWorkerLoop.Result run(Fixture fixture, SessionController controller,
            IOException callbackFailure, boolean requestStop, boolean interrupt, boolean optIn) throws Exception {
        var stopped = new AtomicBoolean();
        var loop = new RootOrdinaryWorkerLoop(new RootOrdinaryWorkerLoop.Configuration("warm-software", 3,
                WALL, Duration.ofSeconds(60), Duration.ofSeconds(1), 16), new RootOrdinaryWorkerLoop.Control() {
            public boolean stopRequested() { return stopped.get(); }
            public void onBatchCompleted(BatchReport report, long next) throws IOException, InterruptedException {
                fixture.completed.add(report);
                if (fixture.completed.size() > 6) throw new IOException("software bounded runaway sentinel");
                if (callbackFailure != null) throw callbackFailure;
                if (interrupt) throw new InterruptedException("software callback interrupt");
                if (requestStop) stopped.set(true);
            }
            public boolean captureCleanPlanningWall(BatchReport actual,long next) throws IOException,InterruptedException {
                if(!optIn)return RootOrdinaryWorkerLoop.Control.super.captureCleanPlanningWall(actual,next);
                fixture.captureCalls++;
                if(fixture.captureFailure!=null)throw fixture.captureFailure;
                // Controlled scheduling stand-in only: no ticket, Root role, actual capture or writer is manufactured.
                return qualifies(controller,actual,next);
            }
        });
        return loop.run(() -> new RootOrdinaryWorkerLoop.BatchCurrent(controller, controller::runBatch), 0);
    }
    private static boolean qualifies(SessionController controller,BatchReport actual) {
        long next=Long.parseLong(actual.batchId().substring(actual.batchId().lastIndexOf('-')+1))+1;
        return qualifies(controller,actual,next);
    }
    private static boolean qualifies(SessionController controller,BatchReport actual,long next) {
        try {
            var method=SessionController.class.getDeclaredMethod("isCleanPlanningWall",BatchReport.class,String.class,long.class);
            method.setAccessible(true);
            return (boolean)method.invoke(controller,actual,"warm-software",next);
        } catch(java.lang.reflect.InvocationTargetException failure) {
            if(failure.getCause() instanceof RuntimeException actualFailure)throw actualFailure;
            if(failure.getCause() instanceof Error actualFailure)throw actualFailure;
            throw new AssertionError(failure.getCause());
        } catch(ReflectiveOperationException failure) {throw new AssertionError(failure);}
    }
    private static BatchLimits limits(String id) { return new BatchLimits(id, 3, WALL, Duration.ofSeconds(60), Duration.ofSeconds(1), 16); }
    private static BatchReport copy(BatchReport x) {
        return new BatchReport(x.session(), x.batchId(), x.terminal(), x.detail(), x.began(), x.ended(), x.phases(), x.turns(),
                x.reconciliations(), x.lifecycleTurns(), x.readPublicationReconciliations(), x.revisionReplans(), x.lastPlan(),
                x.lastTerminalObservation(), x.lastLifecycle(), x.lastSavedPair(), x.committedLedgerHead(), x.committedSavedDays(),
                x.eligibleAdvancesSinceSave(), x.dirtySinceSave(), x.pendingAnalysisBatchIds(), x.completedAnalyses(), x.failedAnalysisBatchIds());
    }
    private static ObservationIdentity observed(BigInteger date, int revision) {
        return new ObservationIdentity(OWNER.machineId(), GAME, new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(31254), BigInteger.valueOf(revision), date),
                "software-frame-" + revision, BigInteger.valueOf(revision), "software-episode"), 3);
    }
    private static CheckpointPair baseline() {
        var save = new CheckpointPair.FileWitness(new ExactRef("D:/software-data-not-opened/save", 1, "b".repeat(64)), new FileStatIdentity(BigInteger.ONE, "1", "0"));
        var driver = new CheckpointPair.FileWitness(new ExactRef("D:/software-data-not-opened/driver", 1, "c".repeat(64)), new FileStatIdentity(BigInteger.ONE, "2", "0"));
        return new CheckpointPair(save, driver, observed(DATE, 1), "software-lineage", 1, "software-prior-save", REF, BASE);
    }
    private static final class TestClock implements SessionClock {
        long nanos;
        public Tick now() { return new Tick(nanos, BASE.plusNanos(nanos)); }
        public void waitFor(Duration duration) { nanos += duration.toNanos(); }
    }
    private static final class Fixture {
        final TestClock clock = new TestClock();
        final List<Mode> modes;
        final List<BigInteger> dates;
        final boolean saved, pending, failJournal;
        final List<BatchReport> completed = new ArrayList<>();
        int captureCalls;
        IOException captureFailure;
        int observations, actions, commits;
        long batchBegan;
        Fixture(List<Mode> modes, List<BigInteger> dates, boolean saved, boolean pending, boolean failJournal) {
            this.modes = modes; this.dates = dates; this.saved = saved; this.pending = pending; this.failJournal = failJournal;
        }
        Mode mode() { return modes.get(Math.min(observations - 1, modes.size() - 1)); }
        private Ready observe(SessionIdentity owner, Instant planningUntil) {
            assertEquals(OWNER, owner); observations++; batchBegan = clock.nanos;
            var identity = observed(dates.get(Math.min(observations - 1, dates.size() - 1)), observations);
            var snapshot = new OpportunityJson.Obj(Map.ofEntries(
                    Map.entry("paused", new OpportunityJson.Bool(true)), Map.entry("map_ready", new OpportunityJson.Bool(true)),
                    Map.entry("revision", new OpportunityJson.IntegerValue(BigInteger.valueOf(observations))),
                    Map.entry("native_revision", new OpportunityJson.IntegerValue(BigInteger.valueOf(observations))),
                    Map.entry("date_raw", new OpportunityJson.IntegerValue(identity.frame().identity().dateRaw())),
                    Map.entry("snapshot_id", new OpportunityJson.Text(identity.frame().snapshotId())),
                    Map.entry("episode_run_id", new OpportunityJson.Text(identity.frame().episodeRunId())),
                    Map.entry("played_character", new OpportunityJson.Obj(Map.of("character_id", new OpportunityJson.IntegerValue(BigInteger.valueOf(31254))))),
                    Map.entry("active_wars", new OpportunityJson.Arr(List.of())), Map.entry("player_armies", new OpportunityJson.Arr(List.of()))));
            List<ExternalFact> facts = pending ? List.of(new ExternalFact("software-unknown", "d".repeat(64), identity,
                    ExternalState.UNKNOWN, UnknownScope.GLOBAL, org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain.marriage,
                    new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), REF)) : List.of();
            var request = new PlanningRequest(identity, new G2Source(OWNER.machineId(), BASE.toString(), "SOFTWARE", REF),
                    OWNER.sessionId(), planningUntil, new PlanningObservation(snapshot, List.of(), Set.of(new OperationKey("life-advance")),
                    Set.of(), Optional.empty(), facts, Optional.empty(), Optional.empty(), false));
            return new Ready(request, CheckpointEligibility.UNAVAILABLE, Optional.empty(), Optional.empty());
        }
        SessionController controller() {
            CheckpointFiles files = new CheckpointFiles() {
                public Optional<CheckpointPair.FileWitness> observe(Path path) { throw unused(); }
                public byte[] read(CheckpointPair.FileWitness witness, int max) { throw unused(); }
                public CheckpointPair.FileWitness replace(Path path, byte[] raw) { throw unused(); }
                public CheckpointPair.FileWitness createNew(Path path, byte[] raw) { throw unused(); }
                public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness source, Path target) { throw unused(); }
            };
            var snapshots = new DriverCheckpointStore.SnapshotSupplier() { public <T> T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) { throw unused(); } };
            var drivers = new DriverCheckpointStore(files, Path.of("D:/software-data-not-opened/driver.json"), "software-only", snapshots);
            CheckpointRequest.ObservationPort noCheckpoint = until -> { throw unused(); };
            var saves = new CheckpointService(files, drivers, noCheckpoint, Path.of("D:/software-data-not-opened/evidence"),
                    Clock.fixed(BASE, ZoneOffset.UTC), (pair, receipt) -> { throw unused(); });
            var requests = new CheckpointRequestFactory(Path.of("D:/software-data-not-opened/save.ck3"), noCheckpoint);
            var realm = new RealmLifecycle(REF);
            var policies = java.util.Arrays.stream(PlanningStage.values()).<OrdinaryPolicy>map(stage -> {
                if (stage == PlanningStage.REALM_MEMBERSHIP_PUBLICATION) return realm;
                return new OrdinaryPolicy() {
                    public PlanningStage stage() { return stage; }
                    public ExactRef implementationSource() { return REF; }
                    public Decision evaluate(PlanningRequest input, Draft previous) {
                        if (stage != PlanningStage.ORDINARY_CORE) return new Keep("unrelated software stage");
                        boolean completesAtWall = mode() == Mode.GENERIC || mode() == Mode.SOURCE_STOP || mode() == Mode.MIGRATION_STOP;
                        clock.nanos = batchBegan + WALL.toNanos() - (completesAtWall ? 0 : 1_000_000_000L);
                        if (mode() == Mode.SOURCE_STOP) return new Stop(PlanningResult.StopReason.SOURCE_CONTRACT_REJECTED, "exact software source failure");
                        if (mode() == Mode.MIGRATION_STOP) return new Stop(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN, "exact software missing chain");
                        if (mode() == Mode.GENERIC || mode() == Mode.COMPLETION_BLOCKED) return new Wait("software ordinary wait");
                        var expected = new ExpectedPostcondition(1, input.before(), input.source(), "software-life-postcondition",
                                List.of(new ExpectedBoolean(new FieldKey("software_only"), true)));
                        var command = new ActionCommand("software-unissued-" + observations, input.before(), input.source(), input.sessionId(),
                                new OperationKey("life-advance"), new OpportunityJson.Obj(Map.of()), expected,
                                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), input.deadline());
                        return new Replace(new Draft("software-policy", "selected", "software unissued Life candidate", Kind.ORDINARY,
                                Optional.of(command), Purpose.DATE_ADVANCE, Optional.empty(), new OpportunityJson.Obj(Map.of())), "software selected unissued Life");
                    }
                };
            }).toList();
            var planner = new OrdinaryPlanner(policies, Clock.fixed(BASE, ZoneOffset.UTC), realm);
            var noActions = new ActionCoordinatorPort() {
                public ActionReceipt execute(ActionCommand command) { actions++; throw unused(); }
                public ActionReceipt reconcile(String actionId) { actions++; throw unused(); }
            };
            var scope = new OrdinaryPlanCompletion.PlanningScope() {
                public <T> ScopeResult<T> inPlanningScope(ScopeWork<T> work) throws IOException, InterruptedException { return new ScopeResult<>(work.run(), Optional.empty()); }
                public PlanningDisposition afterPlanning(PlanningRequest request, PlanningResult planned) {
                    if (mode() == Mode.COMPLETION_BLOCKED || mode() == Mode.AWAITING) {
                        clock.nanos = batchBegan + WALL.toNanos();
                        if (mode() == Mode.COMPLETION_BLOCKED) return new Blocked("exact software completion block", List.of(REF));
                        return new AwaitingOutcome(((PlanningResult.ActionSelected) planned).command());
                    }
                    return new Unchanged("software no publication");
                }
                public ExecutionDisposition afterExecution(ActionReceipt receipt) { throw unused(); }
            };
            var observationsPort = new ObservationPort() {
                public Observation observe(SessionIdentity owner, Instant until) { return Fixture.this.observe(owner, until); }
                public Observation observe(SessionIdentity owner, Instant readinessUntil, Instant planningUntil) { return Fixture.this.observe(owner, planningUntil); }
            };
            var controller = new SessionController(OWNER, (owner, until) -> new GameLifecycle.Running(GAME, REF), observationsPort,
                    planner, noActions, saves, requests, input -> {
                        if (failJournal && input.kind() == JournalKind.BATCH_DEFERRED) throw new IOException("exact software journal marker");
                        commits++; return new JournalCommit(new ExactRef("D:/software-data-not-opened/head-" + commits, 1, String.format("%064x", commits)), 0);
                    }, work -> { throw unused(); }, clock, saved ? Optional.of(baseline()) : Optional.empty(), 0, scope,
                    (owner, receipt, until) -> { throw unused(); });
            controller.bindRetainedIncidents(List::of); return controller;
        }
        private static AssertionError unused() { return new AssertionError("software fixture reached action, physical files, Root issuer or transport"); }
    }
}
