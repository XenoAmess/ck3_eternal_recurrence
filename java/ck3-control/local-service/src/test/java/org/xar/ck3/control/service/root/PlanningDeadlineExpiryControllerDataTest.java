package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;

import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionCoordinatorPort;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Public software ports and the actual Root completion seam; no Runtime context or action issuer is fabricated. */
final class PlanningDeadlineExpiryControllerDataTest {
    private static final Instant BASE = Instant.parse("2026-11-12T14:00:00Z");
    private static final ExactRef REF = new ExactRef("D:/fixture/planning-deadline-source.json", 1, "a".repeat(64));
    private static final GameGeneration GAME = new GameGeneration(123,
            new PythonOnlyUInt64(new BigInteger("134000000000000001")));
    private static final SessionIdentity OWNER = new SessionIdentity("fixture-machine-1", GAME, "planning-deadline");

    @Test void expiryInsideRealPolicyEndsTheOriginalBatchWithoutAnyActionOrSavedCredit() {
        Fixture fixture = new Fixture(FailureShape.PURE);
        SessionController controller = fixture.controller();
        BatchLimits limits = limits("during-policy");
        BatchReport actual = controller.runBatch(limits);
        assertEquals(BatchReport.Terminal.WALL_TIMEOUT, actual.terminal());
        assertFalse(controller.isQuarantined());
        assertEquals(List.of(JournalKind.BATCH_STARTED, JournalKind.BATCH_DEFERRED), fixture.kinds());
        assertEquals(1, fixture.policyCalls);
        assertEquals(0, fixture.afterPlanningCalls, "late planning must not enter another command/publication preparation");
        assertEquals(1, fixture.flushCalls, "the original completion seam still closes the one real software scope");
        assertEquals(Duration.ofSeconds(5).toNanos(), actual.fullWallNanos());
        assertSame(fixture.lastRequest, ((PlanningDeadlineExpiry) fixture.policyFailure).request());
        assertEquals(fixture.lastRequest.deadline(), ((PlanningDeadlineExpiry) fixture.policyFailure).observed());
        assertNoActionsOrCredit(actual, fixture);
        assertSame(actual, controller.runBatch(limits));
        assertEquals(1, fixture.observationCalls, "same batch cannot replan or issue a second observation");
        BatchReport next = controller.runBatch(limits("next-finite-batch"));
        assertEquals(BatchReport.Terminal.WALL_TIMEOUT, next.terminal());
        assertFalse(controller.isQuarantined());
        assertEquals(2, fixture.policyCalls);
        assertNoActionsOrCredit(next, fixture);
    }

    @Test void shorterRequestDeadlineRemainsAnOrdinaryPlannerStopAndTheOriginalEntryCheckStillRuns() {
        Fixture fixture = new Fixture(FailureShape.PURE);
        fixture.requestBudget = Duration.ofSeconds(1);
        SessionController controller = fixture.controller();
        BatchReport actual = controller.runBatch(limits("shorter-request"));
        assertEquals(BatchReport.Terminal.PLANNER_STOPPED, actual.terminal());
        assertTrue(actual.detail().contains("DEADLINE"));
        assertEquals(1, fixture.afterPlanningCalls);
        assertInstanceOf(PlanningResult.Stopped.class, fixture.completedPlan);
        assertEquals(PlanningResult.StopReason.DEADLINE, ((PlanningResult.Stopped) fixture.completedPlan).reason());
        assertFalse(controller.isQuarantined());
        assertEquals(List.of(JournalKind.BATCH_STARTED, JournalKind.BATCH_INTERRUPTED), fixture.kinds());
        assertNoActionsOrCredit(actual, fixture);
        PlanningRequest alreadyExpired = request(fixture.clock.instant());
        assertThrows(ContractViolationException.class, () ->
                new PlanningDeadlineExpiry(alreadyExpired, alreadyExpired.deadline().minusNanos(1)));
        int before = fixture.policyCalls;
        PlanningResult originalEntryStop = fixture.planner.plan(alreadyExpired);
        assertEquals(PlanningResult.StopReason.DEADLINE,
                assertInstanceOf(PlanningResult.Stopped.class, originalEntryStop).reason());
        assertEquals(before, fixture.policyCalls, "pre-existing expired entry does not enter the policy at all");
    }

    @Test void expiredWallClockCannotReclassifyOtherRequestCauseSuppressionOrAnUnrelatedContractFailure() {
        for (FailureShape shape : List.of(FailureShape.OTHER_REQUEST, FailureShape.CAUSE,
                FailureShape.SUPPRESSED, FailureShape.UNRELATED)) {
            Fixture fixture = new Fixture(shape);
            SessionController controller = fixture.controller();
            BatchReport actual = controller.runBatch(limits("not-a-pure-expiry-" + shape));
            assertEquals(BatchReport.Terminal.INTERNAL_FAILURE, actual.terminal(), shape.name());
            assertTrue(controller.isQuarantined(), shape.name());
            assertSame(fixture.policyFailure, fixture.scopeFailure, "original failure object must leave the actual Root seam");
            assertEquals(1, fixture.flushCalls);
            assertEquals(0, fixture.afterPlanningCalls);
            assertEquals(List.of(JournalKind.BATCH_STARTED, JournalKind.BATCH_INTERRUPTED), fixture.kinds());
            if (shape == FailureShape.OTHER_REQUEST) {
                PlanningDeadlineExpiry expiry = (PlanningDeadlineExpiry) fixture.policyFailure;
                assertEquals(fixture.lastRequest, expiry.request());
                assertNotSame(fixture.lastRequest, expiry.request(), "value equality cannot grant exact-request handling");
            } else if (shape == FailureShape.CAUSE) {
                assertSame(fixture.attachedFailure, fixture.policyFailure.getCause());
            } else if (shape == FailureShape.SUPPRESSED) {
                assertArrayEquals(new Throwable[] { fixture.attachedFailure }, fixture.policyFailure.getSuppressed());
            } else assertEquals("unrelated actual policy contract failure", fixture.policyFailure.getMessage());
            assertNoActionsOrCredit(actual, fixture);
        }
    }

    @Test void actualReadPublicationIoFailureMustSurviveExpiryAndMustNotCallTheFailedWriterTwice() {
        Fixture fixture = new Fixture(FailureShape.PURE);
        fixture.publicationFailure = new IOException("original READ publication failed after planning expiry");
        SessionController controller = fixture.controller();
        BatchReport actual = controller.runBatch(limits("expiry-plus-writer-failure"));
        assertEquals(BatchReport.Terminal.WRITER_UNKNOWN, actual.terminal());
        assertTrue(controller.isQuarantined());
        assertEquals(1, fixture.flushCalls, "failed publication is never retried by the completion seam");
        assertEquals(List.of(JournalKind.BATCH_STARTED), fixture.kinds(), "failed writer cannot receive batch completion");
        assertEquals(0, fixture.afterPlanningCalls);
        assertNotNull(fixture.scopeFailure);
        assertTrue(fixture.scopeFailure == fixture.publicationFailure
                        || fixture.scopeFailure.getCause() == fixture.publicationFailure
                        || Arrays.asList(fixture.scopeFailure.getSuppressed()).contains(fixture.publicationFailure),
                "the exact original publication IOException must remain observable");
        assertNoActionsOrCredit(actual, fixture);
    }

    private static BatchLimits limits(String id) {
        return new BatchLimits(id, 1, Duration.ofSeconds(5), Duration.ofSeconds(1), Duration.ofMillis(1), 3);
    }
    private static PlanningRequest request(Instant deadline) {
        var before = new ObservationIdentity(OWNER.machineId(), GAME,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),
                        BigInteger.ONE, BigInteger.valueOf(24000)), "frame-1", BigInteger.ONE, "episode-1"), 1);
        var snapshot = OpportunityJson.object(OpportunityJson.parse(("{\"paused\":true,\"map_ready\":true,\"revision\":1,\"native_revision\":1,\"date_raw\":24000,"
                + "\"snapshot_id\":\"frame-1\",\"episode_run_id\":\"episode-1\",\"played_character\":{\"character_id\":29829},\"active_wars\":[],\"player_armies\":[]}")
                .getBytes(StandardCharsets.UTF_8)), "fixture");
        var observations = new PlanningObservation(snapshot, List.of(), Set.of(new OperationKey("fixture-world-action")),
                Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false);
        return new PlanningRequest(before, new G2Source(OWNER.machineId(), BASE.toString(), "fixture-build", REF),
                OWNER.sessionId(), deadline, observations);
    }
    private static SemanticEvidence semantic(PlanningRequest request) {
        return new SemanticEvidence(request.before(), new ExactRef("D:/fixture/semantic.json", 1, "e".repeat(64)), REF,
                new ExactRef("D:/fixture/driver-stamp.json", 1, "f".repeat(64)),
                new ExactRef("D:/fixture/Driver.json", 1, "c".repeat(64)), BASE);
    }
    private static void assertNoActionsOrCredit(BatchReport actual, Fixture fixture) {
        assertEquals(0, fixture.actionCalls);
        assertTrue(actual.turns().isEmpty());
        assertTrue(actual.reconciliations().isEmpty());
        assertEquals(0, actual.committedSavedDays());
        assertFalse(actual.dirtySinceSave());
        assertTrue(actual.lastSavedPair().isPresent(), "existing software checkpoint baseline is retained");
        assertEquals(1, actual.lastSavedPair().orElseThrow().historyIndex());
    }
    private enum FailureShape { PURE, OTHER_REQUEST, CAUSE, SUPPRESSED, UNRELATED }
    private static final class MutableClock extends Clock implements SessionClock {
        private long nanos;
        @Override public ZoneId getZone() { return ZoneOffset.UTC; }
        @Override public Clock withZone(ZoneId zone) { if (!ZoneOffset.UTC.equals(zone)) throw new IllegalArgumentException("UTC test clock"); return this; }
        @Override public Instant instant() { return BASE.plusNanos(nanos); }
        @Override public Tick now() { return new Tick(nanos, instant()); }
        @Override public void waitFor(Duration elapsed) { nanos += elapsed.toNanos(); }
        void advanceTo(Instant observed) {
            long next = Duration.between(BASE, observed).toNanos();
            assertTrue(next >= nanos);
            nanos = next;
        }
    }
    private static final class Fixture {
        final MutableClock clock = new MutableClock();
        final FailureShape failureShape;
        final List<JournalInput> journal = new ArrayList<>();
        Duration requestBudget;
        int actionCalls, observationCalls, policyCalls, afterPlanningCalls, flushCalls;
        PlanningRequest lastRequest;
        PlanningResult completedPlan;
        RuntimeException policyFailure;
        Throwable scopeFailure;
        Throwable attachedFailure;
        IOException publicationFailure;
        OrdinaryPlanner planner;
        Fixture(FailureShape failureShape) { this.failureShape = failureShape; }
        List<JournalKind> kinds() { return journal.stream().map(JournalInput::kind).toList(); }
        SessionController controller() {
            RealmLifecycle realm = new RealmLifecycle(REF);
            List<OrdinaryPolicy> policies = Arrays.stream(PlanningStage.values()).<OrdinaryPolicy>map(stage -> {
                if (stage == PlanningStage.REALM_MEMBERSHIP_PUBLICATION) return realm;
                return new OrdinaryPolicy() {
                    @Override public PlanningStage stage() { return stage; }
                    @Override public ExactRef implementationSource() { return REF; }
                    @Override public Decision evaluate(PlanningRequest actual, Draft previous) {
                        if (stage != PlanningStage.ORDINARY_CORE) return new Keep("test preserves original policy order");
                        policyCalls++;
                        lastRequest = actual;
                        clock.advanceTo(actual.deadline());
                        if (failureShape == FailureShape.UNRELATED) {
                            policyFailure = new ContractViolationException("unrelated actual policy contract failure");
                        } else {
                            PlanningRequest owner = failureShape == FailureShape.OTHER_REQUEST
                                    ? new PlanningRequest(actual.before(), actual.source(), actual.sessionId(), actual.deadline(), actual.observations())
                                    : actual;
                            PlanningDeadlineExpiry expiry = new PlanningDeadlineExpiry(owner, clock.instant());
                            if (failureShape == FailureShape.CAUSE) {
                                attachedFailure = new IllegalStateException("original preparation cause");
                                expiry.initCause(attachedFailure);
                            } else if (failureShape == FailureShape.SUPPRESSED) {
                                attachedFailure = new IOException("original suppressed publication failure");
                                expiry.addSuppressed(attachedFailure);
                            }
                            policyFailure = expiry;
                        }
                        throw policyFailure;
                    }
                };
            }).toList();
            planner = new OrdinaryPlanner(policies, clock, realm);
            CheckpointFiles files = new CheckpointFiles() {
                @Override public Optional<CheckpointPair.FileWitness> observe(Path path) { throw unused(); }
                @Override public byte[] read(CheckpointPair.FileWitness witness, int maximum) { throw unused(); }
                @Override public CheckpointPair.FileWitness replace(Path path, byte[] raw) { throw unused(); }
                @Override public CheckpointPair.FileWitness createNew(Path path, byte[] raw) { throw unused(); }
                @Override public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness source, Path target) { throw unused(); }
            };
            DriverCheckpointStore.SnapshotSupplier snapshots = new DriverCheckpointStore.SnapshotSupplier() {
                @Override public <T> T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) { throw unused(); }
            };
            var drivers = new DriverCheckpointStore(files, Path.of("D:/fixture/unused-Driver.json"), "planning-deadline-only", snapshots);
            CheckpointRequest.ObservationPort noCheckpoint = until -> { throw unused(); };
            var checkpoints = new CheckpointService(files, drivers, noCheckpoint, Path.of("D:/fixture/unused-evidence"), clock,
                    (pair, receipt) -> { throw unused(); });
            var requests = new CheckpointRequestFactory(Path.of("D:/fixture/unused.ck3"), noCheckpoint);
            ActionCoordinatorPort noActions = new ActionCoordinatorPort() {
                @Override public ActionReceipt execute(ActionCommand command) { actionCalls++; throw unused(); }
                @Override public ActionReceipt reconcile(String id) { actionCalls++; throw unused(); }
            };
            OrdinaryPlanCompletion.PlanningScope scope = new OrdinaryPlanCompletion.PlanningScope() {
                @Override public <T> ScopeResult<T> inPlanningScope(ScopeWork<T> work) throws IOException, InterruptedException {
                    try {
                        return RootReadPublicationCompletion.finishOriginalWork(work, () -> {
                            flushCalls++;
                            if (publicationFailure != null) throw publicationFailure;
                            return Optional.empty();
                        }, () -> false);
                    } catch (IOException | InterruptedException | RuntimeException | Error failure) {
                        scopeFailure = failure;
                        throw failure;
                    }
                }
                @Override public PlanningDisposition afterPlanning(PlanningRequest original, PlanningResult actual) {
                    afterPlanningCalls++;
                    completedPlan = actual;
                    return new Unchanged("no software publication is needed");
                }
                @Override public ExecutionDisposition afterExecution(ActionReceipt actual) { throw unused(); }
            };
            BatchJournal writer = input -> { journal.add(input); return new JournalCommit(REF, 0); };
            ObservationPort observer = new ObservationPort() {
                @Override public Observation observe(SessionIdentity owner, Instant deadline) { return ready(owner, deadline); }
                @Override public Observation observe(SessionIdentity owner, Instant readinessDeadline, Instant planningDeadline) {
                    return ready(owner, planningDeadline);
                }
                private Observation ready(SessionIdentity owner, Instant deadline) {
                    assertEquals(OWNER, owner);
                    observationCalls++;
                    Instant chosen = requestBudget == null ? deadline : clock.instant().plus(requestBudget);
                    PlanningRequest actual = request(chosen);
                    return new Ready(actual, CheckpointEligibility.SAFE, Optional.empty(), Optional.of(semantic(actual)));
                }
            };
            var baseline = new CheckpointPair(
                    new CheckpointPair.FileWitness(new ExactRef("D:/fixture/existing.ck3", 1, "b".repeat(64)),
                            new FileStatIdentity(BigInteger.ONE, "9007199254740993", "134000000000000001")),
                    new CheckpointPair.FileWitness(new ExactRef("D:/fixture/Driver.json", 1, "c".repeat(64)),
                            new FileStatIdentity(BigInteger.ONE, "9007199254740995", "134000000000000003")),
                    request(BASE.plusSeconds(5)).before(), "lineage-1", 1, "save-initial", REF, BASE);
            SessionController controller = new SessionController(OWNER,
                    (owner, until) -> new GameLifecycle.Running(GAME, REF), observer, planner, noActions,
                    checkpoints, requests, writer, work -> { throw unused(); }, clock, Optional.of(baseline), 0, scope,
                    (owner, receipt, until) -> { throw unused(); });
            controller.bindRetainedIncidents(List::of);
            return controller;
        }
        private static AssertionError unused() { return new AssertionError("planning-only regression reached an action, SAVE, or unrelated producer"); }
    }
}
