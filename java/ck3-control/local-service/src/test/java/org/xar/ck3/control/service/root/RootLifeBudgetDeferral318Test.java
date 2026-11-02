package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.checkpoint.CheckpointPair;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanTrace;
import org.xar.ck3.control.application.session.BatchReport;
import org.xar.ck3.control.application.session.SessionClock;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.FileStatIdentity;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Public scheduling DATA only. The synthetic pair label grants no physical pair or Root authority. */
final class RootLifeBudgetDeferral318Test {
    private static final Instant START = Instant.parse("2026-11-02T00:00:00Z");
    private static final String DEFER = "PRE_INTENT_LIFE_BUDGET_DEFERRED: remaining_nanos=200000000000; reserve_nanos=600000000000; no action INTENT submitted; next batch must freshly observe and plan";
    private static final GameGeneration GAME = new GameGeneration(123, new PythonOnlyUInt64(BigInteger.valueOf(100)));
    private static final SessionIdentity OWNER = new SessionIdentity("software-budget", GAME, "software-session");
    private static final ExactRef REF = new ExactRef("D:/software-data-not-opened/evidence", 1, "1".repeat(64));

    @Test void onlyExactLifeCleanZeroDispatchReportGetsTheSingleFreshBatchOpportunity() {
        var actual = report("life-advance", 10, 31, 1, "software-episode", BatchReport.Terminal.WALL_TIMEOUT, DEFER, false, true, List.of());
        var selected = actual.lastPlan().orElseThrow().finalPlan().orElseThrow().command().orElseThrow();
        byte[] original = ActionCodec.encodeCommand(selected);
        assertTrue(RootOrdinaryWorkerLoop.isUnissuedLifeBudgetDeferral(actual));
        assertTrue(actual.fullWallNanos() < java.time.Duration.ofMinutes(20).toNanos());
        assertArrayEquals(original, ActionCodec.encodeCommand(selected));
        assertEquals(START.plusSeconds(1200), selected.deadline());
        assertTrue(actual.turns().isEmpty());
        assertEquals(0, actual.committedSavedDays());
        for (String operation : List.of("life-advance-fake", "resume-map", "save-checkpoint", "assign-councillor"))
            assertFalse(RootOrdinaryWorkerLoop.isUnissuedLifeBudgetDeferral(report(operation, 10, 31, 1, "software-episode", BatchReport.Terminal.WALL_TIMEOUT, DEFER, false, true, List.of())), operation);
        assertFalse(RootOrdinaryWorkerLoop.isUnissuedLifeBudgetDeferral(report("life-advance", 10, 31, 1, "software-episode", BatchReport.Terminal.CHECKPOINT_UNKNOWN, DEFER, false, true, List.of())));
        assertFalse(RootOrdinaryWorkerLoop.isUnissuedLifeBudgetDeferral(report("life-advance", 10, 31, 1, "software-episode", BatchReport.Terminal.WALL_TIMEOUT, "complete batch monotonic wall bound expired", false, true, List.of())));
        assertFalse(RootOrdinaryWorkerLoop.isUnissuedLifeBudgetDeferral(report("life-advance", 10, 31, 1, "software-episode", BatchReport.Terminal.WALL_TIMEOUT, DEFER, true, true, List.of())));
        assertFalse(RootOrdinaryWorkerLoop.isUnissuedLifeBudgetDeferral(report("life-advance", 10, 31, 1, "software-episode", BatchReport.Terminal.WALL_TIMEOUT, DEFER, false, false, List.of())));
        var action = new BatchReport.PhaseSpan(BatchReport.Phase.ACTION, new SessionClock.Tick(999_000_000_000L, START.plusSeconds(999)),
                new SessionClock.Tick(1_000_000_000_000L, START.plusSeconds(1000)), BatchReport.PhaseTerminal.RETURNED);
        assertFalse(RootOrdinaryWorkerLoop.isUnissuedLifeBudgetDeferral(report("life-advance", 10, 31, 1, "software-episode", BatchReport.Terminal.WALL_TIMEOUT, DEFER, false, true, List.of(action))));
    }

    @Test void readRevisionChangesCannotResetConsecutiveSameDayBudgetDeferrals() {
        var first = report("life-advance", 10, 31, 1, "software-episode", BatchReport.Terminal.WALL_TIMEOUT, DEFER, false, true, List.of());
        var newRead = report("life-advance-one-day", 10, 31, 99, "software-episode", BatchReport.Terminal.WALL_TIMEOUT, DEFER, false, true, List.of());
        assertTrue(RootOrdinaryWorkerLoop.sameUnissuedLifeBudgetScope(first, newRead));
        assertFalse(RootOrdinaryWorkerLoop.sameUnissuedLifeBudgetScope(first,
                report("life-advance", 11, 31, 99, "software-episode", BatchReport.Terminal.WALL_TIMEOUT, DEFER, false, true, List.of())));
        assertFalse(RootOrdinaryWorkerLoop.sameUnissuedLifeBudgetScope(first,
                report("life-advance", 10, 32, 99, "software-episode", BatchReport.Terminal.WALL_TIMEOUT, DEFER, false, true, List.of())));
        assertFalse(RootOrdinaryWorkerLoop.sameUnissuedLifeBudgetScope(first,
                report("life-advance", 10, 31, 99, "software-next-episode", BatchReport.Terminal.WALL_TIMEOUT, DEFER, false, true, List.of())));
    }

    private static BatchReport report(String operation, long date, long actor, long revision, String episode,
            BatchReport.Terminal terminal, String detail, boolean dirty, boolean retainPair, List<BatchReport.PhaseSpan> phases) {
        var observed = new ProposalLifecycle.ObservationIdentity(OWNER.machineId(), GAME,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(actor), BigInteger.valueOf(revision), BigInteger.valueOf(date)),
                        "software-native:" + revision, BigInteger.valueOf(revision), episode), 3);
        var source = new G2Source(OWNER.machineId(), START.toString(), "software-build", REF);
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, observed, source, "software-scheduling-data",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("software_only"), true)));
        var command = new ActionCommand("software-unissued-" + revision, observed, source, OWNER.sessionId(), new OperationKey(operation),
                new OpportunityJson.Obj(Map.of()), expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), START.plusSeconds(1200));
        var draft = new OrdinaryPolicy.Draft("software-policy", "selected", "software scheduling DATA", OrdinaryPolicy.Kind.ORDINARY,
                Optional.of(command), OrdinaryPolicy.Purpose.DATE_ADVANCE, Optional.empty(), new OpportunityJson.Obj(Map.of()));
        var trace = new PlanTrace(observed, List.of(), Optional.of(draft));
        var save = new CheckpointPair.FileWitness(new ExactRef("D:/software-data-not-opened/save", 1, "2".repeat(64)), new FileStatIdentity(BigInteger.ONE, "1", "0"));
        var driver = new CheckpointPair.FileWitness(new ExactRef("D:/software-data-not-opened/driver", 1, "3".repeat(64)), new FileStatIdentity(BigInteger.ONE, "2", "0"));
        var pair = new CheckpointPair(save, driver, observed, "software-lineage", 1, "software-prior-save", REF, START);
        return new BatchReport(OWNER, "software-budget-" + revision, terminal, detail,
                new SessionClock.Tick(0, START), new SessionClock.Tick(1_000_000_000_000L, START.plusSeconds(1000)),
                phases, List.of(), List.of(), List.of(), List.of(), List.of(), Optional.of(trace), Optional.empty(), Optional.empty(),
                retainPair ? Optional.of(pair) : Optional.empty(), Optional.of(REF), 0, 0, dirty, List.of(), List.of(), List.of());
    }
}
