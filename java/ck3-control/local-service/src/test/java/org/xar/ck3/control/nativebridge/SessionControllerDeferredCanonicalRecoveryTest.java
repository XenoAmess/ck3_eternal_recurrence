package org.xar.ck3.control.nativebridge;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.OriginalWindowReducer;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import static org.xar.ck3.control.application.session.SessionPorts.*;

/**
 * Tests that a real SessionController runBatch timeout produces a canonical BATCH_DEFERRED event,
 * which is then recovered by the actual ContinuityBatchJournal's initial no-dispatch recovery mechanism.
 * No fake journals, stores, or authorities are used.
 */
final class SessionControllerDeferredCanonicalRecoveryTest {
    @TempDir Path root;

    @Test void sessionControllerTimeoutProducesCanonicalDeferredRecovery() throws Exception {
        // 1. Setup actual fixture with real writer, archive, and transitions
        var initialFrame = new ActionWriterIntegrationFixture.SoftwareActionScenario(new OperationKey("pause-map"), "game.command.pause-map",
            (command, attempt, dispatch) -> new ActionPorts.Pending("no action is dispatched", List.of(attempt.guard().nativeEvidence())),
            () -> {}, Optional.empty(), Optional.empty(), true, Optional.empty());
        try (var fixture = new ActionWriterIntegrationFixture(root.resolve("timeout"), false, initialFrame)) {
        var owner = fixture.observationIdentity();
        var source = fixture.observationSource();

        // 2. Create actual OrdinaryCycleTransitions and register on writer
        var cycles = new OrdinaryCycleTransitions(
            fixture.archive,
            (same, session, semantic) -> { throw new AssertionError("timeout recovery does not verify semantic"); },
            (same, session, pair, proof) -> { throw new AssertionError("timeout recovery does not save"); },
            new OriginalWindowReducer.Policy(10958),
            fixture.writer::requireSession
        );
        for (String kind : cycles.kinds()) {
            fixture.bindAdditionalTransitionAuthority(kind, cycles);
        }
        var batches = new ContinuityBatchJournal(fixture.writer, cycles);

        // 3. Create a mutable SessionClock that advances only during planning
        var clockRef = new AtomicReference<>(new SessionClock.Tick(0, Instant.now()));
        var mutableClock = new SessionClock() {
            @Override public Tick now() { return clockRef.get(); }
            @Override public void waitFor(Duration duration) throws InterruptedException {
                // Do not sleep, just advance the virtual clock
                var current = clockRef.get();
                clockRef.set(new Tick(current.elapsedNanos() + duration.toNanos(), current.utc().plus(duration)));
            }
        };

        // 4. Create a real SessionController with complete planning policies
        var realm = new RealmLifecycle(source.sourceRef());
        var policies = java.util.Arrays.stream(PlanningStage.values()).<OrdinaryPolicy>map(stage -> {
            if (stage == PlanningStage.REALM_MEMBERSHIP_PUBLICATION) return realm;
            return new OrdinaryPolicy() {
                @Override public PlanningStage stage() { return stage; }
                @Override public ExactRef implementationSource() { return source.sourceRef(); }
                @Override public Decision evaluate(PlanningRequest input, Draft previous) {
                    // Advance the clock during ORDINARY_CORE to trigger timeout
                    if (stage == PlanningStage.ORDINARY_CORE) {
                        var current = clockRef.get();
                        clockRef.set(new SessionClock.Tick(current.elapsedNanos() + 61_000_000_000L, current.utc().plusSeconds(61)));
                    }
                    return new Keep("timeout test policy");
                }
            };
        }).toList();

        var planner = new OrdinaryPlanner(policies, Clock.fixed(clockRef.get().utc(), java.time.ZoneOffset.UTC), realm);

        // 5. Create a real ObservationPort that uses the actual fixture collector
        var observationPort = new ObservationPort() {
            @Override public Observation observe(SessionIdentity expected, Instant deadline) throws IOException, InterruptedException {
                // Use the actual fixture collector with the provided deadline
                var ready = fixture.collector.observe(expected, deadline);
                return ready;
            }
        };

        // 6. Create a real CheckpointService that throws on any save attempt
        var checkpointFiles = new CheckpointFiles() {
            @Override public Optional<CheckpointPair.FileWitness> observe(Path path) { throw new AssertionError("timeout test must not save"); }
            @Override public byte[] read(CheckpointPair.FileWitness witness, int maximum) { throw new AssertionError("timeout test must not save"); }
            @Override public CheckpointPair.FileWitness replace(Path path, byte[] bytes) { throw new AssertionError("timeout test must not save"); }
            @Override public CheckpointPair.FileWitness createNew(Path path, byte[] bytes) { throw new AssertionError("timeout test must not save"); }
            @Override public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness witness, Path path) { throw new AssertionError("timeout test must not save"); }
        };
        var snapshotSupplier = new DriverCheckpointStore.SnapshotSupplier() {
            @Override public <T> T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) { throw new AssertionError("timeout test must not save"); }
        };
        var drivers = new DriverCheckpointStore(checkpointFiles, root.resolve("unused-driver.json"), "unused-pipe", snapshotSupplier);
        var readiness = new CheckpointRequest.ObservationPort() {
            @Override public CheckpointRequest.Readiness observe(Instant deadline) { throw new AssertionError("timeout test must not save"); }
        };
        var checkpoints = new CheckpointService(checkpointFiles, drivers, readiness, root.resolve("unused-evidence"), Clock.systemUTC(),
            (pair, receipt) -> { throw new AssertionError("timeout test must not save"); });

        // 7. Create a real OrdinaryPlanCompletion that does not publish
        var completionCalls = new AtomicInteger();
        var completion = new OrdinaryPlanCompletion.PlanningScope() {
            @Override public <T> ScopeResult<T> inPlanningScope(ScopeWork<T> work) throws IOException, InterruptedException {
                return new ScopeResult<>(work.run(), Optional.empty());
            }
            @Override public PlanningDisposition afterPlanning(PlanningRequest original, PlanningResult planned) {
                completionCalls.incrementAndGet();
                return new OrdinaryPlanCompletion.Blocked("an expired planner must not reach domain completion", List.of(source.sourceRef()));
            }
            @Override public ExecutionDisposition afterExecution(ActionReceipt actual) {
                return new OrdinaryPlanCompletion.Unchanged("timeout test no execution");
            }
        };

        // 8. Create the SessionController
        var controller = new SessionController(
            owner,
            (actual, deadline) -> new GameLifecycle.Running(owner.game(), source.sourceRef()),
            observationPort,
            planner,
            fixture.coordinator,
            checkpoints,
            new CheckpointRequestFactory(root.resolve("unused.ck3"), readiness),
            batches,
            work -> { throw new AssertionError("timeout test no analysis"); },
            mutableClock,
            Optional.empty(),
            0,
            completion,
            (actual, parent, deadline) -> { throw new AssertionError("timeout test no episode"); }
        );
        controller.bindRetainedIncidents(List::of);
        controller.bindRestartDriver(fixture.physicalInputs().driverAssembler());

        // 9. Establish a legitimate baseline capture at prefix "timeout-worker", next 0
        assertInstanceOf(Ready.class, fixture.collector.observe(owner, Instant.now().plusSeconds(60)));
        controller.drainForCleanRestart(Instant.now().plusSeconds(60));
        var baselineTicket = fixture.writer.locked(same -> {
            return controller.captureCleanRestart(same, "timeout-worker", 0);
        });
        assertNotNull(baselineTicket);
        var baselineAdmission = fixture.writer.locked(same -> batches.admitCleanRestart(same, baselineTicket));
        var baselineState = fixture.writer.locked(same -> same.head().state());
        clockRef.set(new SessionClock.Tick(0, Instant.now()));

        // 10. Run a real batch with finite 60-second wall/readiness budget
        var limits = new BatchLimits("timeout-worker-0", 10, Duration.ofSeconds(60), Duration.ofSeconds(60), Duration.ofSeconds(1), 3);
        var report = controller.runBatch(limits);

        // 11. Assert the batch timed out and produced a canonical deferred event
        assertEquals(BatchReport.Terminal.WALL_TIMEOUT, report.terminal(), () -> "actual terminal: " + report.terminal() + " detail: " + report.detail());
        assertEquals(0, completionCalls.get(), "expired planner result must be classified before domain completion");
        assertEquals(0, report.turns().size(), "timeout must not execute actions");
        assertEquals(0, report.committedSavedDays(), "timeout must not save");
        assertFalse(report.dirtySinceSave(), "timeout must not mark dirty");
        assertFalse(controller.isQuarantined(), "timeout must not quarantine");

        // 12. Verify the canonical state has BATCH_DEFERRED and sequence increased
        var stateAfterTimeout = fixture.writer.locked(same -> same.head().state());
        assertEquals(baselineState.sequence() + 2, stateAfterTimeout.sequence(), "Controller itself emits STARTED and DEFERRED");
        assertEquals(baselineState.settledCycles(), stateAfterTimeout.settledCycles());
        assertEquals(baselineState.settledDateRaw(), stateAfterTimeout.settledDateRaw());
        assertThrows(IllegalArgumentException.class, () -> fixture.writer.locked(same -> batches.admitCleanRestart(same, baselineTicket)));
        assertEquals(ContinuityState.Status.RUNNING, stateAfterTimeout.status(), "deferred batch keeps RUNNING status");
        var boundary = stateAfterTimeout.toJson().get(WriterContracts.ORDINARY_BATCH_BOUNDARY_FIELD);
        assertNotNull(boundary);
        assertEquals(JournalKind.BATCH_DEFERRED.name(), StrictJson.text(boundary.get("boundary")), "actual deferred boundary");
        assertEquals("timeout-worker-0", StrictJson.text(boundary.get("batch_id")), "actual deferred batch ID");

        // 13. Perform actual initial no-dispatch recovery on the captured suffix
        var recovery = fixture.writer.locked(same -> batches.admitInitialNoDispatchRecovery(same, owner));
        assertNotNull(recovery);
        assertTrue(recovery.capturedController().isPresent(), "recovery must capture the controller state");
        assertEquals(1, recovery.nextBatchSequence(), "recovery advances to next batch sequence");
        assertTrue(recovery.consumedBatchIds().contains("timeout-worker-0"), "recovery consumes the deferred batch");

        // 14. Finish the recovery with a fresh semantic evidence (using actual collector)
        var timeoutHeadDigest = fixture.writer.locked(same -> same.head().digest());
        var freshReady = fixture.collector.observe(owner, Instant.now().plusSeconds(60));
        var semantic = assertInstanceOf(Ready.class, freshReady).semanticEvidence().orElseThrow();
        fixture.writer.locked(same -> {
            batches.finishInitialNoDispatchRecovery(same, recovery, semantic);
            return null;
        });

        // 15. Verify the recovery closed the batch without another mutation
        var stateAfterRecovery = fixture.writer.locked(same -> same.head().state());
        assertEquals(stateAfterTimeout.sequence(), stateAfterRecovery.sequence(), "recovery does not add new events");
        assertEquals(timeoutHeadDigest, fixture.writer.locked(same -> same.head().digest()), "recovery preserves the canonical head");

        // 16. Restore a replacement controller through the actual recovery admission
        var replacement = new SessionController(
            owner,
            (actual, deadline) -> new GameLifecycle.Running(owner.game(), source.sourceRef()),
            observationPort,
            planner,
            fixture.coordinator,
            checkpoints,
            new CheckpointRequestFactory(root.resolve("unused.ck3"), readiness),
            batches,
            work -> { throw new AssertionError("replacement no analysis"); },
            new SessionClock.SystemClock(),
            Optional.empty(),
            0,
            completion,
            (actual, parent, deadline) -> { throw new AssertionError("replacement no episode"); }
        );
        replacement.bindRetainedIncidents(List::of);
        replacement.bindRestartDriver(fixture.physicalInputs().driverAssembler());

        fixture.writer.locked(same -> {
            replacement.restoreInitialNoDispatchRecovery(same, recovery);
            return null;
        });

        // 17. Verify the replacement controller has the consumed batch and next sequence
        replacement.drainForCleanRestart(Instant.now().plusSeconds(60));
        var replacementTicket = fixture.writer.locked(same -> {
            return replacement.captureCleanRestart(same, "timeout-worker", 1);
        });
        assertNotNull(replacementTicket);
        var replacementAdmitted = fixture.writer.locked(same -> batches.admitCleanRestart(same, replacementTicket));
        assertTrue(replacementAdmitted.controller().usedBatches().contains("timeout-worker-0"), "replacement preserves consumed batch");
        assertEquals(1, replacementAdmitted.controller().nextBatchSequence(), "replacement advances to next sequence");
        assertEquals(0, replacementAdmitted.controller().totalCommittedDays(), "replacement preserves zero saved days");
        assertFalse(replacementAdmitted.controller().dirty(), "replacement preserves clean state");
        var originalController = baselineAdmission.controller();
        var restoredController = replacementAdmitted.controller();
        assertEquals(originalController.savedPair(), restoredController.savedPair());
        assertEquals(originalController.eligibleSinceSave(), restoredController.eligibleSinceSave());
        assertEquals(originalController.unsavedGameplayActions(), restoredController.unsavedGameplayActions());
        assertEquals(originalController.completedAnalysisIds(), restoredController.completedAnalysisIds());
        assertArrayEquals(baselineAdmission.facts().driver().encode(), replacementAdmitted.facts().driver().encode());
        assertEquals(baselineAdmission.facts().stamp(), replacementAdmitted.facts().stamp());
        assertEquals(baselineAdmission.facts().actionRows(), replacementAdmitted.facts().actionRows());
        assertEquals(baselineAdmission.facts().auxiliary(), replacementAdmitted.facts().auxiliary());
        assertEquals(baselineAdmission.facts().loop(), replacementAdmitted.facts().loop());

        // 18. Verify no native actions were written
        assertEquals(0, fixture.nativeActionWrites(), "timeout recovery must not write native actions");
        }
    }
}
