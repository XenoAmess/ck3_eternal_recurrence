package org.xar.ck3.control.application.session;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.campaign.M7CampaignPolicies.RealmLifecycle;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;

/** Pure advisory DATA through the real public Controller; all execution ports refuse. */
public final class LifeBudgetHint334Test {
    private static final Instant AT = Instant.parse("2026-11-02T19:00:00Z");
    private static final GameGeneration GAME = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
    private static final SessionIdentity OWNER = new SessionIdentity("fixture-machine-1", GAME, "hint-334");
    private static final ExactRef REF = new ExactRef("D:/fixture/never-opened-334", 1, "a".repeat(64));
    private static final BatchLimits LIMITS = new BatchLimits("hint-334", 1, Duration.ofSeconds(1200), Duration.ofSeconds(60), Duration.ofMillis(1), 1);

    @Test void qualifiedRestoreSurvivesNewControllerWithoutInflatingReadinessOrGrantingAnyPort() {
        var subject = frame(GAME, 11, "episode-1", 240);
        RawJson hint = hint(OWNER, subject, "800000000000", "905000000000");
        var original = controller();
        assertEquals(600_000_000_000L, original.retainedLifeBudgetReserveNanos(LIMITS, subject));
        assertTrue(original.restoreLifeBudgetHint(hint));
        assertTrue(original.restoreLifeBudgetHint(hint));
        assertEquals(905_000_000_000L, original.retainedLifeBudgetReserveNanos(LIMITS, subject));
        Optional<RawJson> retained = Optional.of(hint);
        for (int i = 0; i < 20; i++) retained = SessionController.retainLifeBudgetHint(report(frame(GAME, 11, "episode-1", 264)), retained);
        assertTrue(retained.isPresent());
        var decoded = StrictJson.parse(retained.orElseThrow().bytes());
        assertEquals("800000000000", decoded.get("saved_life_tail_nanos").textValue());
        assertEquals("905000000000", decoded.get("reserve_floor_nanos").textValue());
        var replacement = controller();
        assertTrue(replacement.restoreLifeBudgetHint(retained.orElseThrow()));
        assertEquals(905_000_000_000L, replacement.retainedLifeBudgetReserveNanos(LIMITS, frame(GAME, 11, "episode-1", 288)));
        assertFalse(replacement.isRunning()); assertFalse(replacement.isQuarantined()); assertFalse(replacement.isRetired());
        assertTrue(replacement.lastReport().isEmpty()); assertTrue(replacement.savedPair().isEmpty());
    }

    @Test void invalidOwnerAndAtUseChangedSubjectPreserveTheOriginalFallback() {
        var subject = frame(GAME, 11, "episode-1", 240);
        for (SessionIdentity wrong : List.of(new SessionIdentity("other-machine", GAME, OWNER.sessionId()),
                new SessionIdentity(OWNER.machineId(), new GameGeneration(124, GAME.creationFiletime()), OWNER.sessionId()),
                new SessionIdentity(OWNER.machineId(), new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("134000000000000002"))), OWNER.sessionId()),
                new SessionIdentity(OWNER.machineId(), GAME, "another-session"))) {
            var fresh = controller(); assertFalse(fresh.restoreLifeBudgetHint(hint(wrong, subject, "800000000000", "905000000000")));
            assertEquals(600_000_000_000L, fresh.retainedLifeBudgetReserveNanos(LIMITS, subject));
        }
        for (String invalid : List.of("-1", "01", "86400000000001", "9999999999999999999"))
            assertFalse(controller().restoreLifeBudgetHint(hint(OWNER, subject, invalid, "0")));
        var restored = controller(); assertTrue(restored.restoreLifeBudgetHint(hint(OWNER, subject, "800000000000", "905000000000")));
        for (ObservationIdentity other : List.of(frame(GAME, 12, "episode-1", 264), frame(GAME, 11, "episode-2", 264),
                frame(GAME, 11, "episode-1", 216), frame(new GameGeneration(124, GAME.creationFiletime()), 11, "episode-1", 264)))
            assertEquals(600_000_000_000L, restored.retainedLifeBudgetReserveNanos(LIMITS, other));
        assertTrue(SessionController.retainLifeBudgetHint(report(frame(GAME, 12, "episode-1", 264)),
                Optional.of(hint(OWNER, subject, "800000000000", "905000000000"))).isEmpty());
    }

    private static ObservationIdentity frame(GameGeneration game, int actor, String episode, int date) {
        return new ObservationIdentity(OWNER.machineId(), game, new JointBudgetSelector.ProposalFrame(
                new JointBudgetSelector.Frame(BigInteger.valueOf(actor), BigInteger.ONE, BigInteger.valueOf(date)),
                "hint-frame-334", BigInteger.ONE, episode), 1);
    }
    private static RawJson hint(SessionIdentity owner, ObservationIdentity subject, String tail, String floor) {
        var row = StrictJson.object().put("schema", "xar.life-budget-hint/v1");
        row.set("owner", OrdinaryCycleTransitions.sessionToJson(owner)); row.set("subject", ProposalLifecycleCodec.observation(subject));
        row.put("saved_life_tail_nanos", tail); row.put("reserve_floor_nanos", floor); return new RawJson(StrictJson.canonical(row));
    }
    private static BatchReport report(ObservationIdentity frame) {
        var stamp = new FileStatIdentity(BigInteger.ONE, "100", "134000000000000001");
        var pair = new CheckpointPair(new CheckpointPair.FileWitness(REF, stamp),
                new CheckpointPair.FileWitness(new ExactRef("D:/fixture/never-opened-driver-334", 1, "b".repeat(64)), stamp),
                frame, "hint-lineage", 1, "hint-save", REF, AT);
        var tick = new SessionClock.Tick(0, AT);
        return new BatchReport(OWNER, "hint-report", BatchReport.Terminal.WALL_TIMEOUT, "controlled clean scheduling report", tick, tick,
                List.of(), List.of(), List.of(), List.of(), List.of(), List.of(), Optional.empty(), Optional.empty(), Optional.empty(),
                Optional.of(pair), Optional.empty(), 0, 0, false, List.of(), List.of(), List.of());
    }
    /** Existing public DATA fixture pattern; no file, writer, planning, clock or action operation is allowed. */
    private static SessionController controller() {
        CheckpointFiles files = new CheckpointFiles() {
            @Override public Optional<CheckpointPair.FileWitness> observe(Path path) { throw new AssertionError("no file observation"); }
            @Override public byte[] read(CheckpointPair.FileWitness witness, int maximum) { throw new AssertionError("no file read"); }
            @Override public CheckpointPair.FileWitness replace(Path path, byte[] bytes) { throw new AssertionError("no file replace"); }
            @Override public CheckpointPair.FileWitness createNew(Path path, byte[] bytes) { throw new AssertionError("no file create"); }
            @Override public CheckpointPair.FileWitness copyNew(CheckpointPair.FileWitness source, Path target) { throw new AssertionError("no file copy"); }
        };
        var drivers = new DriverCheckpointStore(files, Path.of("D:/fixture/unused-driver-334.json"), "hint-334",
                new DriverCheckpointStore.SnapshotSupplier() {
                    @Override public <T> T withFrozen(DriverCheckpointStore.SnapshotWork<T> work) { throw new AssertionError("no Driver freeze"); }
                });
        CheckpointRequest.ObservationPort noCheckpoint = until -> { throw new AssertionError("no checkpoint observation"); };
        var checkpoints = new CheckpointService(files, drivers, noCheckpoint, Path.of("D:/fixture/unused-evidence-334"),
                Clock.fixed(AT, ZoneOffset.UTC), (pair, receipt) -> { throw new AssertionError("no seed adoption"); });
        ActionCoordinatorPort actions = new ActionCoordinatorPort() {
            @Override public ActionReceipt execute(ActionCommand command) { throw new AssertionError("no execute"); }
            @Override public ActionReceipt reconcile(String actionId) { throw new AssertionError("no reconcile"); }
        };
        OrdinaryPlanCompletion.PlanningScope completion = new OrdinaryPlanCompletion.PlanningScope() {
            @Override public <T> ScopeResult<T> inPlanningScope(ScopeWork<T> work) { throw new AssertionError("no planning scope"); }
            @Override public PlanningDisposition afterPlanning(PlanningRequest request, PlanningResult result) { throw new AssertionError("no planning"); }
            @Override public ExecutionDisposition afterExecution(ActionReceipt receipt) { throw new AssertionError("no outcome consumption"); }
        };
        SessionClock noClock = new SessionClock() {
            @Override public Tick now() { throw new AssertionError("no run clock"); }
            @Override public void waitFor(Duration duration) { throw new AssertionError("no wait"); }
        };
        return new SessionController(OWNER, (same, until) -> { throw new AssertionError("no lifecycle"); },
                (same, until) -> { throw new AssertionError("no Ready"); },
                new OrdinaryPlanner(List.of(), Clock.fixed(AT, ZoneOffset.UTC), new RealmLifecycle(REF)), actions, checkpoints,
                new CheckpointRequestFactory(Path.of("D:/fixture/unused-334.ck3"), noCheckpoint),
                input -> { throw new AssertionError("no journal"); }, batch -> { throw new AssertionError("no analysis"); },
                noClock, Optional.empty(), 0, completion, (same, receipt, until) -> { throw new AssertionError("no episode continuation"); });
    }
}
