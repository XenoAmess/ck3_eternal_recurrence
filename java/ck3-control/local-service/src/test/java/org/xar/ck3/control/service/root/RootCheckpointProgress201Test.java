package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionCoordinatorPort;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.checkpoint.CheckpointFiles;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.checkpoint.CheckpointRequest;
import org.xar.ck3.control.application.checkpoint.CheckpointRequestFactory;
import org.xar.ck3.control.application.checkpoint.CheckpointService;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.planning.OrdinaryPlanCompletion;
import org.xar.ck3.control.application.planning.OrdinaryPlanner;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.session.BatchLimits;
import org.xar.ck3.control.application.session.BatchReport;
import org.xar.ck3.control.application.session.SessionClock;
import org.xar.ck3.control.application.session.SessionController;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import static org.junit.jupiter.api.Assertions.*;

/** Loop scheduling DATA only. Controller business, physical files and Native ports must never run. */
final class RootCheckpointProgress201Test {
    private static final Instant TIME = Instant.parse("2026-10-28T00:00:00Z");
    private static final SessionIdentity OWNER = new SessionIdentity("loop-data-machine",
            new GameGeneration(1, new PythonOnlyUInt64(BigInteger.valueOf(100))), "loop-data-session");
    private static final ExactRef HEAD = new ExactRef("fixture-ledger-head", 1, "1".repeat(64));
    private static final Duration WALL = Duration.ofMillis(1_200_000);

    @Test void internalSaveOnlyBatchPermitsContinuation() throws Exception {
        var requested = new ArrayList<BatchLimits>();
        var reports = new ArrayList<BatchReport>();
        var nextSequences = new ArrayList<Long>();
        var stop = new AtomicBoolean();
        var calls = new AtomicInteger();
        var controller = dormantController();
        var historical = historicalPairData();
        var control = new RootOrdinaryWorkerLoop.Control() {
            @Override public boolean stopRequested() { return stop.get(); }
            @Override public void onBatchCompleted(BatchReport report, long nextBatchSequence) {
                reports.add(report); nextSequences.add(nextBatchSequence);
                if (reports.size() == 2) stop.set(true);
            }
        };
        var loop = new RootOrdinaryWorkerLoop(configuration(), control);
        RootOrdinaryWorkerLoop.BatchAccess access = () -> new RootOrdinaryWorkerLoop.BatchCurrent(controller, limits -> {
            int index = calls.incrementAndGet();
            assertTrue(index <= 2, "bounded software scheduler must stop after its second callback");
            requested.add(limits);
            return report(limits.batchId(), index == 1 ? 8 : 0, Optional.of(HEAD), Optional.of(historical));
        });

        var result = loop.run(access, 7);

        System.out.println("Loop201 codeSource=" + RootOrdinaryWorkerLoop.class.getProtectionDomain().getCodeSource().getLocation()
                + " reportedSavedDays=" + reports.stream().map(BatchReport::committedSavedDays).toList()
                + " stopReason=" + result.stopReason() + " failureDetail=" + result.failureDetail());
        assertEquals(2, calls.get()); assertEquals(2, reports.size());
        assertEquals(List.of(8L, 9L), nextSequences);
        assertEquals("save-only-7", requested.get(0).batchId());
        assertEquals("save-only-8", requested.get(1).batchId());
        assertNotEquals(requested.get(0).batchId(), requested.get(1).batchId());
        assertNotSame(requested.get(0), requested.get(1));
        for (var limits : requested) {
            assertEquals(WALL, limits.wallTime());
            assertEquals(1_200_000, limits.wallTime().toMillis());
            assertEquals(2, limits.maximumTurns());
        }
        var first = reports.getFirst();
        assertEquals(8, first.committedSavedDays());
        assertTrue(first.turns().isEmpty()); assertTrue(first.reconciliations().isEmpty());
        assertTrue(first.lifecycleTurns().isEmpty()); assertTrue(first.readPublicationReconciliations().isEmpty());
        assertTrue(first.revisionReplans().isEmpty()); assertEquals(Optional.of(HEAD), first.committedLedgerHead());
        assertEquals(Optional.of(historical), first.lastSavedPair());
        assertEquals(RootOrdinaryWorkerLoop.StopReason.OPERATOR_STOP, result.stopReason());
        assertEquals(9, result.nextBatchSequence());
        assertSame(reports.getLast(), result.lastReport().orElseThrow());
        assertTrue(result.failureDetail().isEmpty()); assertFalse(controller.isQuarantined());
    }

    @Test void zeroWorkBatchStopsNoProgress() throws Exception {
        var calls = new AtomicInteger();
        var nextSequences = new ArrayList<Long>();
        var reports = new ArrayList<BatchReport>();
        var controller = dormantController();
        var historical = historicalPairData();
        var loop = new RootOrdinaryWorkerLoop(configuration(), new RootOrdinaryWorkerLoop.Control() {
            @Override public boolean stopRequested() { return false; }
            @Override public void onBatchCompleted(BatchReport report, long nextBatchSequence) {
                reports.add(report); nextSequences.add(nextBatchSequence);
            }
        });
        RootOrdinaryWorkerLoop.BatchAccess access = () -> new RootOrdinaryWorkerLoop.BatchCurrent(controller, limits -> {
            assertEquals(1, calls.incrementAndGet(), "zero work must not enter a second batch");
            assertEquals(WALL, limits.wallTime());
            return report(limits.batchId(), 0, Optional.of(HEAD), Optional.of(historical));
        });

        var result = loop.run(access, 7);

        assertEquals(1, calls.get()); assertEquals(1, reports.size());
        assertEquals(List.of(8L), nextSequences);
        assertEquals(RootOrdinaryWorkerLoop.StopReason.NO_PROGRESS, result.stopReason());
        assertEquals(8, result.nextBatchSequence());
        assertSame(reports.getFirst(), result.lastReport().orElseThrow());
        assertEquals(Optional.of(HEAD), reports.getFirst().committedLedgerHead());
        assertEquals(Optional.of(historical), reports.getFirst().lastSavedPair());
        assertEquals(0, reports.getFirst().committedSavedDays());
        assertTrue(result.failureDetail().isEmpty()); assertFalse(controller.isQuarantined());
    }

    private static RootOrdinaryWorkerLoop.Configuration configuration() {
        return new RootOrdinaryWorkerLoop.Configuration("save-only", 2, WALL,
                Duration.ofSeconds(5), Duration.ofMillis(100), 10);
    }

    private static BatchReport report(String batchId, long savedDays, Optional<ExactRef> head, Optional<CheckpointPair> pair) {
        var tick = new SessionClock.Tick(0, TIME);
        return new BatchReport(OWNER, batchId, BatchReport.Terminal.TURN_BOUND, "synthetic scheduling boundary",
                tick, tick, List.of(), List.of(), List.of(), List.of(), List.of(), List.of(),
                Optional.empty(), Optional.empty(), Optional.empty(), pair, head, savedDays, 0, false,
                List.of(), List.of(), List.of());
    }

    /** Public, unverified report DATA. These refs are never opened or treated as physical SAVE credit. */
    private static CheckpointPair historicalPairData() {
        var frame = new ObservationIdentity(OWNER.machineId(), OWNER.game(), new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.ONE, BigInteger.valueOf(24000)),
                "historical-snapshot", BigInteger.ONE, "historical-episode"), 1);
        var save = new CheckpointPair.FileWitness(new ExactRef("historical-save.ck3", 1, "2".repeat(64)),
                new FileStatIdentity(BigInteger.ONE, "1", "1"));
        var driver = new CheckpointPair.FileWitness(new ExactRef("historical-driver.json", 1, "3".repeat(64)),
                new FileStatIdentity(BigInteger.ONE, "2", "1"));
        return new CheckpointPair(save, driver, frame, "historical-lineage", 1, "historical-save-action", HEAD, TIME);
    }

    private static SessionController dormantController() {
        var unused = Path.of("D:/loop-data-fixture201");
        CheckpointFiles files = new CheckpointFiles() {
            @Override public Optional<CheckpointPair.FileWitness> observe(Path path) { throw unexpected(); }
            @Override public byte[] read(CheckpointPair.FileWitness witness, int maximum) { throw unexpected(); }
            @Override public CheckpointPair.FileWitness replace(Path path, byte[] bytes) { throw unexpected(); }
            @Override public CheckpointPair.FileWitness createNew(Path path, byte[] bytes) { throw unexpected(); }
            @Override public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness witness, Path path) { throw unexpected(); }
        };
        var snapshots = new DriverCheckpointStore.SnapshotSupplier() {
            @Override public <T> T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) { throw unexpected(); }
        };
        var drivers = new DriverCheckpointStore(files, unused.resolve("driver.json"), "loop-unused-pipe", snapshots);
        CheckpointRequest.ObservationPort observations = until -> { throw unexpected(); };
        var checkpoints = new CheckpointService(files, drivers, observations, unused.resolve("evidence"), Clock.systemUTC(),
                (pair, receipt) -> { throw unexpected(); });
        var realm = new RealmLifecycle(HEAD);
        var policies = Arrays.stream(PlanningStage.values()).<OrdinaryPolicy>map(stage -> {
            if (stage == PlanningStage.REALM_MEMBERSHIP_PUBLICATION) return realm;
            return new OrdinaryPolicy() {
                @Override public PlanningStage stage() { return stage; }
                @Override public ExactRef implementationSource() { return HEAD; }
                @Override public Decision evaluate(PlanningRequest request, Draft previous) { throw unexpected(); }
            };
        }).toList();
        var actions = new ActionCoordinatorPort() {
            @Override public ActionReceipt execute(ActionCommand command) { throw unexpected(); }
            @Override public ActionReceipt reconcile(String actionId) { throw unexpected(); }
        };
        var completion = new OrdinaryPlanCompletion.PlanningScope() {
            @Override public <T> ScopeResult<T> inPlanningScope(ScopeWork<T> work) throws IOException, InterruptedException { throw unexpected(); }
            @Override public PlanningDisposition afterPlanning(PlanningRequest request, PlanningResult result) { throw unexpected(); }
            @Override public ExecutionDisposition afterExecution(ActionReceipt receipt) { throw unexpected(); }
        };
        return new SessionController(OWNER, (owner, until) -> { throw unexpected(); },
                (owner, until) -> { throw unexpected(); }, new OrdinaryPlanner(policies, Clock.systemUTC(), realm),
                actions, checkpoints, new CheckpointRequestFactory(unused.resolve("save.ck3"), observations),
                input -> { throw unexpected(); }, work -> { throw unexpected(); }, new SessionClock.SystemClock(),
                Optional.empty(), 0, completion, (owner, receipt, until) -> { throw unexpected(); });
    }

    private static AssertionError unexpected() {
        return new AssertionError("Loop scheduling DATA must not execute Controller business, physical files or Native");
    }
}
