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
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.*;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

import org.xar.ck3.control.application.session.*;
import org.xar.ck3.control.application.advance.LifeAdvanceComposite;

/** Public Controller ports and package worker-loop seam; no RootSessionAccess/private restore issuer, physical SAVE, CK3, or timing claim. */
final class RootAnnualDirtyLifeBudgetTest {
    private static final Instant BASE = Instant.parse("2026-11-04T00:00:00Z");
    private static final long SAVED_DATE = 53_154_744L;
    private static final ExactRef REF = new ExactRef("D:/annual-fixture/native.json", 1, "a".repeat(64));
    private static final GameGeneration GAME = new GameGeneration(123,
            new PythonOnlyUInt64(new BigInteger("134000000000000001")));
    private static final SessionIdentity OWNER = new SessionIdentity("annual-fixture", GAME, "annual-session");


    @Test void historicalDirtyStateStillChecksTheNextFreshLifeBeforeSubmission() {
        Fixture f = dirtyFixture(); SessionController controller = f.controller();
        BatchReport seeded = controller.runBatch(limits("dirty-seed", 1));
        assertEquals(BatchReport.Terminal.TURN_BOUND, seeded.terminal(), seeded::detail);
        assertTrue(seeded.dirtySinceSave()); assertEquals(1, seeded.eligibleAdvancesSinceSave());
        f.lifePlanningCostNanos = Duration.ofSeconds(20).toNanos();
        BatchReport deferred = controller.runBatch(limits("dirty-next-life", 4));
        assertDeferred(deferred, f, 1, 0);
        assertTrue(deferred.dirtySinceSave()); assertEquals(1, deferred.eligibleAdvancesSinceSave());
        assertEquals(f.baseline, deferred.lastSavedPair().orElseThrow());
        assertEquals(f.baseline, controller.savedPair().orElseThrow());
        assertEquals(0, deferred.committedSavedDays());
        assertTrue(RootOrdinaryWorkerLoop.isUnissuedLifeBudgetDeferral(deferred));
    }

    @Test void anEarlierSettledTurnCannotBypassTheReserveForANewLifeInTheSameBatch() {
        Fixture f = dirtyFixture(); f.lifePlanningCostNanos = Duration.ofSeconds(20).toNanos();
        BatchReport report = f.controller().runBatch(limits("same-batch-new-life", 4));
        assertDeferred(report, f, 1, 1);
        assertTrue(report.turns().getFirst().receipt().settled());
        assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED, report.turns().getFirst().receipt().outcome());
        assertTrue(RootOrdinaryWorkerLoop.isUnissuedLifeBudgetDeferral(report));
    }

    @Test void aDirtyUnissuedLifeGetsOneFreshBatchThenStopsWithoutProgress() throws Exception {
        Fixture f = dirtyFixture(); SessionController controller = f.controller();
        controller.runBatch(limits("loop-seed", 1));
        f.lifePlanningCostNanos = Duration.ofSeconds(20).toNanos();
        List<BatchReport> reports = new ArrayList<>();
        RootOrdinaryWorkerLoop.Result result = loop(controller, reports, f, false);
        assertEquals(2, reports.size()); assertEquals(2, result.nextBatchSequence());
        assertEquals(RootOrdinaryWorkerLoop.StopReason.NO_PROGRESS, result.stopReason());
        for (BatchReport report : reports) assertDeferred(report, f, 1, 0);
        assertTrue(result.failureDetail().orElseThrow().contains("second consecutive"));
        var first = reports.get(0).lastPlan().orElseThrow().finalPlan().orElseThrow().command().orElseThrow();
        var second = reports.get(1).lastPlan().orElseThrow().finalPlan().orElseThrow().command().orElseThrow();
        assertNotSame(first, second); assertTrue(first.deadline().isBefore(second.deadline()));
    }

    @Test void actualSameDateGameplayResetsTheDeferralButTheNextEmptyBatchStillStops() throws Exception {
        Fixture f = dirtyFixture(); f.advanceRaw = 0; SessionController controller = f.controller();
        controller.runBatch(limits("progress-seed", 1));
        f.lifePlanningCostNanos = Duration.ofSeconds(20).toNanos();
        List<BatchReport> reports = new ArrayList<>();
        RootOrdinaryWorkerLoop.Result result = loop(controller, reports, f, true);
        assertEquals(3, reports.size(), "real same-date progress must reset the previous deferral too");
        assertEquals(RootOrdinaryWorkerLoop.StopReason.NO_PROGRESS, result.stopReason());
        assertEquals(3, result.nextBatchSequence()); assertEquals(2, f.actions);
        assertEquals(0, reports.get(0).turns().size()); assertEquals(1, reports.get(1).turns().size());
        assertEquals(0, reports.get(2).turns().size());
        assertTrue(reports.get(1).turns().getFirst().receipt().visibleGameplay());
        assertEquals(reports.get(0).lastPlan().orElseThrow().before().frame().identity().dateRaw(),
                reports.get(1).lastPlan().orElseThrow().before().frame().identity().dateRaw());
        for (BatchReport report : reports) {
            assertTrue(report.dirtySinceSave()); assertEquals(0, report.committedSavedDays());
            assertTrue(RootOrdinaryWorkerLoop.isUnissuedLifeBudgetDeferral(report));
        }
        assertEquals(0, f.saveAdmissions);
    }

    @Test void consumerRejectsDispatchAfterTheLastPlanAndNonReturnedPlanning() {
        Fixture f = dirtyFixture(); f.lifePlanningCostNanos = Duration.ofSeconds(20).toNanos();
        BatchReport report = f.controller().runBatch(limits("consumer-negative", 4));
        assertTrue(RootOrdinaryWorkerLoop.isUnissuedLifeBudgetDeferral(report));
        var phases = new ArrayList<>(report.phases());
        var tick = new SessionClock.Tick(21_000_000_000L, BASE.plusSeconds(21));
        phases.add(new BatchReport.PhaseSpan(BatchReport.Phase.ACTION, tick, tick, BatchReport.PhaseTerminal.RETURNED));
        assertFalse(RootOrdinaryWorkerLoop.isUnissuedLifeBudgetDeferral(copyReport(report, phases)));
        phases = new ArrayList<>(report.phases());
        phases.add(new BatchReport.PhaseSpan(BatchReport.Phase.PLANNING, tick, tick, BatchReport.PhaseTerminal.FAILED));
        assertFalse(RootOrdinaryWorkerLoop.isUnissuedLifeBudgetDeferral(copyReport(report, phases)));
        assertFalse(RootOrdinaryWorkerLoop.isUnissuedLifeBudgetDeferral(copyReport(report, List.of())));
    }

    @Test void aFreshLifeWithEnoughReserveStillSubmitsAndRetainsTheAnnualDirtyTail() {
        Fixture f = dirtyFixture(); f.customActionsBeforeLife = 0;
        BatchReport report = f.controller().runBatch(limits("enough-life-budget", 1));
        assertEquals(BatchReport.Terminal.TURN_BOUND, report.terminal(), report::detail);
        assertEquals(1, f.actions); assertEquals(1, report.turns().size());
        assertTrue(report.turns().getFirst().receipt().settled()); assertTrue(report.dirtySinceSave());
        assertFalse(RootOrdinaryWorkerLoop.isUnissuedLifeBudgetDeferral(report));
        assertEquals(0, f.saveAdmissions); assertEquals(0, report.committedSavedDays());
    }

    @Test void consumerRejectsAnAlreadyIssuedSelectedIdAndAnyUnsettledPriorReceipt() {
        Fixture duplicate = dirtyFixture(); duplicate.reuseFirstActionId = true;
        duplicate.lifePlanningCostNanos = Duration.ofSeconds(20).toNanos();
        BatchReport issued = duplicate.controller().runBatch(limits("issued-selected-id", 4));
        assertDeferred(issued, duplicate, 1, 1);
        assertEquals(issued.turns().getFirst().receipt().command().actionId(),
                issued.lastPlan().orElseThrow().finalPlan().orElseThrow().command().orElseThrow().actionId());
        assertFalse(RootOrdinaryWorkerLoop.isUnissuedLifeBudgetDeferral(issued));
        Fixture f = dirtyFixture(); f.lifePlanningCostNanos = Duration.ofSeconds(20).toNanos();
        BatchReport report = f.controller().runBatch(limits("unsettled-prior-data", 4));
        var prior = report.turns().getFirst();
        var unknown = new ActionReceipt(1, 1, prior.receipt().command(), ActionCodec.bodySha256(prior.receipt().command()),
                new ActionState.Unknown(Optional.empty(), Optional.empty(), "public DATA unresolved original", List.of(REF)));
        var unsettled = new BatchReport.Turn(1, prior.before(), prior.plan(), unknown,
                new TurnFacts(false, false, List.of(REF)));
        assertFalse(RootOrdinaryWorkerLoop.isUnissuedLifeBudgetDeferral(copyReport(report, report.phases(), List.of(unsettled))));
    }

    private static Fixture dirtyFixture() { Fixture f = new Fixture(true); f.advanceRaw = 24; return f; }
    private static BatchLimits limits(String id, int turns) {
        return new BatchLimits(id, turns, Duration.ofSeconds(30), Duration.ofSeconds(1), Duration.ofMillis(1), 100_000);
    }
    private static void assertDeferred(BatchReport report, Fixture f, int actions, int currentTurns) {
        assertEquals(BatchReport.Terminal.WALL_TIMEOUT, report.terminal(), report::detail);
        assertTrue(report.detail().startsWith("PRE_INTENT_LIFE_BUDGET_DEFERRED: "), report::detail);
        assertEquals(actions, f.actions, "the newly selected Life must not reach ActionCoordinatorPort.execute");
        assertEquals(currentTurns, report.turns().size()); assertEquals(0, f.saveAdmissions);
        assertEquals(0, report.committedSavedDays());
        assertTrue(f.journal.stream().noneMatch(row -> row.kind() == JournalKind.SAVE_CONFIRMED));
    }
    private static RootOrdinaryWorkerLoop.Result loop(SessionController controller, List<BatchReport> reports,
            Fixture f, boolean progressAfterFirst) throws Exception {
        var config = new RootOrdinaryWorkerLoop.Configuration("annual-reserve", 4, Duration.ofSeconds(30),
                Duration.ofSeconds(1), Duration.ofMillis(1), 100_000);
        var control = new RootOrdinaryWorkerLoop.Control() {
            @Override public boolean stopRequested() { return false; }
            @Override public void onBatchCompleted(BatchReport report, long nextSequence) {
                reports.add(report); assertTrue(reports.size() <= 4, "worker must not retry without a finite bound");
                if (progressAfterFirst && reports.size() == 1) f.customActionsBeforeLife = 2;
            }
        };
        return new RootOrdinaryWorkerLoop(config, control).run(
                () -> new RootOrdinaryWorkerLoop.BatchCurrent(controller, controller::runBatch), 0);
    }
    private static BatchReport copyReport(BatchReport source, List<BatchReport.PhaseSpan> phases) {
        return copyReport(source, phases, source.turns());
    }
    private static BatchReport copyReport(BatchReport source, List<BatchReport.PhaseSpan> phases, List<BatchReport.Turn> turns) {
        var tick = new SessionClock.Tick(0, BASE);
        return new BatchReport(source.session(), "public-consumer-negative", source.terminal(), source.detail(), tick, tick,
                phases, turns, source.reconciliations(), source.lifecycleTurns(), source.readPublicationReconciliations(),
                source.revisionReplans(), source.lastPlan(), Optional.empty(), Optional.empty(), source.lastSavedPair(),
                Optional.of(REF), 0, source.eligibleAdvancesSinceSave(), source.dirtySinceSave(), List.of(), List.of(), List.of());
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
        int actions, saveAdmissions, customActionsBeforeLife = 1;
        long lifePlanningCostNanos;
        final List<ActionCommand> plannedCommands = new ArrayList<>();
        boolean unknown, reuseFirstActionId;
        CheckpointEligibility eligibility = CheckpointEligibility.SAFE, afterEligibility = CheckpointEligibility.SAFE;
        Fixture(boolean withBaseline) {
            this.withBaseline = withBaseline;
            var save = new ExactRef("D:/annual-fixture/save.ck3", 1, "b".repeat(64));
            var driver = new ExactRef("D:/annual-fixture/Driver.json", 1, "c".repeat(64));
            baseline = new CheckpointPair(new CheckpointPair.FileWitness(save,
                    new FileStatIdentity(BigInteger.ONE, "9007199254740993", "134000000000000001")),
                    new CheckpointPair.FileWitness(driver,
                    new FileStatIdentity(BigInteger.ONE, "9007199254740995", "134000000000000003")),
                    request(BASE.plusSeconds(10)).before(), "annual-lineage", 1, "saved-original", REF, BASE);
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
                    List.of(), Set.of(new OperationKey("annual-fixture-action"), new OperationKey("life-advance")), Set.of(), Optional.empty(), List.of(), Optional.empty(), Optional.empty(), false);
            return new PlanningRequest(before, new G2Source(OWNER.machineId(), BASE.toString(), "annual-fixture", REF), OWNER.sessionId(), deadline, observation);
        }
        SemanticEvidence semantic(PlanningRequest request) {
            return new SemanticEvidence(request.before(), new ExactRef("D:/annual-fixture/semantic.json", 1, "d".repeat(64)), REF,
                    new ExactRef("D:/annual-fixture/stamp.json", 1, "e".repeat(64)), baseline.driver().reference(), BASE);
        }
        ActionCommand command(PlanningRequest request) {
            return new ActionCommand("annual-action-" + (reuseFirstActionId ? 1 : actions + 1), request.before(), request.source(), OWNER.sessionId(),
                    new OperationKey(actions < customActionsBeforeLife ? "annual-fixture-action" : "life-advance"), new OpportunityJson.Obj(Map.of()),
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
                    return new CompletedCycleProof(actions, evidence, "f".repeat(64));
                }
            };
            OrdinaryPlanCompletion.PlanningScope scope = new OrdinaryPlanCompletion.PlanningScope() {
                @Override public <T> ScopeResult<T> inPlanningScope(ScopeWork<T> work) throws IOException, InterruptedException {
                    return new ScopeResult<>(work.run(), Optional.empty());
                }
                @Override public PlanningDisposition afterPlanning(PlanningRequest request, PlanningResult planned) {
                    if (planned instanceof PlanningResult.ActionSelected selected) {
                        plannedCommands.add(selected.command());
                        if (LifeAdvanceComposite.accepts(selected.command().operation().value())) clock.nanos += lifePlanningCostNanos;
                    }
                    return new Unchanged("annual reserve DATA fixture");
                }
                @Override public ExecutionDisposition afterExecution(ActionReceipt receipt) { return new Unchanged("annual DATA fixture"); }
            };
            ObservationPort observer = new ObservationPort() {
                @Override public Observation observe(SessionIdentity owner, Instant until) {
                    var request = request(until);
                    return new Ready(request, eligibility, Optional.empty(), Optional.of(semantic(request)));
                }
                @Override public Observation observe(SessionIdentity owner, Instant readinessUntil, Instant planningUntil) {
                    assertFalse(planningUntil.isBefore(readinessUntil));
                    var request = request(planningUntil);
                    return new Ready(request, eligibility, Optional.empty(), Optional.of(semantic(request)));
                }
            };
            var controller = new SessionController(OWNER, (owner, until) -> new GameLifecycle.Running(GAME, REF), observer,
                    planner, actionPort, checkpoints, requests, writer, work -> { throw unused(); }, clock,
                    withBaseline ? Optional.of(baseline) : Optional.empty(), 0, scope, (owner, receipt, until) -> { throw unused(); });
            controller.bindRetainedIncidents(List::of);
            return controller;
        }
        private static AssertionError unused() { return new AssertionError("fixture must not perform physical SAVE, Game or unrelated work"); }
    }
}
