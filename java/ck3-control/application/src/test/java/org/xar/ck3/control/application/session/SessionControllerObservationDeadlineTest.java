package org.xar.ck3.control.application.session;

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
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionCoordinatorPort;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.GameLifecycle;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;

/** Real Controller execution at its ObservationPort boundary; no Game or native endpoint is used. */
final class SessionControllerObservationDeadlineTest {
    private static final Instant BASE = Instant.parse("2026-10-30T00:00:00Z");
    private static final ExactRef REF = new ExactRef("D:/fixture/readiness-source.json", 1, "a".repeat(64));
    private static final GameGeneration GAME = new GameGeneration(123,
            new PythonOnlyUInt64(new BigInteger("134000000000000001")));
    private static final SessionIdentity OWNER = new SessionIdentity("fixture-machine-1", GAME, "readiness-deadline");

    @Test void threeHundredSecondBatchPassesSixtySecondDeadlineToTheActualObservationPort() {
        Fixture fixture = new Fixture();
        fixture.observer = (owner, until) -> {
            assertEquals(OWNER, owner);
            fixture.deadlines.add(until);
            fixture.clock.advanceTo(until); // The downstream operation consumes exactly its received bound.
            return new Waiting("downstream readiness bound reached", REF);
        };
        SessionController controller = fixture.controller();
        BatchReport actual = controller.runBatch(limits("readiness60", 300, 60));
        assertEquals(List.of(BASE.plusSeconds(60)), fixture.deadlines,
                "the actual observer must receive readinessTimeout, not the complete batch deadline");
        assertEquals(BatchReport.Terminal.READINESS_TIMEOUT, actual.terminal());
        assertEquals(Duration.ofSeconds(60).toNanos(), actual.fullWallNanos());
        assertEquals(JournalKind.BATCH_DEFERRED, fixture.journal.getLast().kind());
        assertFalse(controller.isQuarantined());
        assertNoGameplay(actual, fixture);
        assertSame(actual, controller.runBatch(limits("readiness60", 300, 60)));
        assertEquals(1, fixture.deadlines.size(), "same batch returns its original result without observing again");
    }

    @Test void repeatedReadinessPollsKeepTheOriginalOperationDeadline() {
        Fixture fixture = new Fixture();
        fixture.observer = (owner, until) -> {
            fixture.deadlines.add(until);
            if (fixture.deadlines.size() == 1) fixture.clock.waitFor(Duration.ofSeconds(20));
            else fixture.clock.advanceTo(until);
            return new Waiting("still waiting", REF);
        };
        BatchReport actual = fixture.controller().runBatch(limits("same-window", 300, 60));
        assertEquals(List.of(BASE.plusSeconds(60), BASE.plusSeconds(60)), fixture.deadlines);
        assertEquals(BatchReport.Terminal.READINESS_TIMEOUT, actual.terminal());
        assertEquals(Duration.ofSeconds(60).toNanos(), actual.fullWallNanos());
        assertNoGameplay(actual, fixture);
    }

    @Test void shorterCompleteBatchDeadlineRemainsTheFinalWallTimeout() {
        Fixture fixture = new Fixture();
        fixture.observer = (owner, until) -> {
            fixture.deadlines.add(until);
            fixture.clock.advanceTo(until);
            return new Waiting("batch exhausted", REF);
        };
        SessionController controller = fixture.controller();
        BatchReport actual = controller.runBatch(limits("batch20", 20, 60));
        assertEquals(List.of(BASE.plusSeconds(20)), fixture.deadlines);
        assertEquals(BatchReport.Terminal.WALL_TIMEOUT, actual.terminal());
        assertEquals(Duration.ofSeconds(20).toNanos(), actual.fullWallNanos());
        assertEquals(JournalKind.BATCH_DEFERRED, fixture.journal.getLast().kind());
        assertFalse(controller.isQuarantined());
        assertNoGameplay(actual, fixture);
    }

    @Test void elapsedBatchWorkCapsTheRemainingReadinessOperationAtFortySeconds() {
        Fixture fixture = new Fixture();
        fixture.startDelay = Duration.ofSeconds(260);
        fixture.observer = (owner, until) -> {
            assertEquals(BASE.plusSeconds(260), fixture.clock.now().utc());
            fixture.deadlines.add(until);
            fixture.clock.advanceTo(until);
            return new Waiting("remaining batch exhausted", REF);
        };
        BatchReport actual = fixture.controller().runBatch(limits("remaining40", 300, 60));
        assertEquals(List.of(BASE.plusSeconds(300)), fixture.deadlines,
                "260 seconds of actual preceding batch work leaves a 40 second operation bound");
        assertEquals(BatchReport.Terminal.WALL_TIMEOUT, actual.terminal());
        assertEquals(Duration.ofSeconds(300).toNanos(), actual.fullWallNanos());
        assertNoGameplay(actual, fixture);
    }

    private static BatchLimits limits(String id, long wallSeconds, long readinessSeconds) {
        return new BatchLimits(id, 1, Duration.ofSeconds(wallSeconds), Duration.ofSeconds(readinessSeconds),
                Duration.ofSeconds(1), 3);
    }
    private static void assertNoGameplay(BatchReport actual, Fixture fixture) {
        assertTrue(actual.turns().isEmpty());
        assertTrue(actual.reconciliations().isEmpty());
        assertEquals(0, actual.committedSavedDays());
        assertEquals(0, fixture.actionCalls);
        assertFalse(actual.dirtySinceSave());
        assertTrue(actual.lastSavedPair().isEmpty());
    }
    private static final class TestClock implements SessionClock {
        private long nanos;
        @Override public Tick now() { return new Tick(nanos, BASE.plusNanos(nanos)); }
        @Override public void waitFor(Duration duration) { nanos += duration.toNanos(); }
        void advanceTo(Instant until) {
            long target = Duration.between(BASE, until).toNanos();
            assertTrue(target >= nanos, "the observer received an already expired deadline");
            nanos = target;
        }
    }
    private static final class Fixture {
        final TestClock clock = new TestClock();
        final List<Instant> deadlines = new ArrayList<>();
        final List<JournalInput> journal = new ArrayList<>();
        int actionCalls;
        Duration startDelay = Duration.ZERO;
        ObservationPort observer;

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
            var drivers = new DriverCheckpointStore(files, Path.of("D:/fixture/unused-Driver.json"), "readiness-only", snapshots);
            CheckpointRequest.ObservationPort noCheckpoint = until -> { throw unused(); };
            var checkpoints = new CheckpointService(files, drivers, noCheckpoint, Path.of("D:/fixture/unused-evidence"),
                    Clock.fixed(BASE, ZoneOffset.UTC), (pair, receipt) -> { throw unused(); });
            var requests = new CheckpointRequestFactory(Path.of("D:/fixture/unused.ck3"), noCheckpoint);
            var planner = new OrdinaryPlanner(List.of(), Clock.fixed(BASE, ZoneOffset.UTC), new RealmLifecycle(REF));
            ActionCoordinatorPort noActions = new ActionCoordinatorPort() {
                @Override public ActionReceipt execute(ActionCommand command) { actionCalls++; throw unused(); }
                @Override public ActionReceipt reconcile(String id) { actionCalls++; throw unused(); }
            };
            OrdinaryPlanCompletion.PlanningScope scope = new OrdinaryPlanCompletion.PlanningScope() {
                @Override public <T> ScopeResult<T> inPlanningScope(ScopeWork<T> work) throws IOException, InterruptedException {
                    return new ScopeResult<>(work.run(), Optional.empty());
                }
                @Override public PlanningDisposition afterPlanning(PlanningRequest request, PlanningResult planned) { throw unused(); }
                @Override public ExecutionDisposition afterExecution(ActionReceipt actual) { throw unused(); }
            };
            BatchJournal writer = input -> {
                journal.add(input);
                if (input.kind() == JournalKind.BATCH_STARTED) clock.waitFor(startDelay);
                return new JournalCommit(REF, 0);
            };
            var controller = new SessionController(OWNER, (owner, until) -> new GameLifecycle.Running(GAME, REF),
                    observer, planner, noActions, checkpoints, requests, writer, work -> { throw unused(); }, clock,
                    Optional.empty(), 0, scope, (owner, receipt, until) -> { throw unused(); });
            controller.bindRetainedIncidents(List::of);
            return controller;
        }
        private static AssertionError unused() { return new AssertionError("observation-only regression reached gameplay or SAVE"); }
    }
}
