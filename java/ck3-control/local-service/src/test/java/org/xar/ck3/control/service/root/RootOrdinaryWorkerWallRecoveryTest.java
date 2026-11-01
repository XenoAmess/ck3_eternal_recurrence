package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.lang.reflect.Proxy;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.ActionPorts;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionReceiptCodec;
import org.xar.ck3.control.application.action.ActionState;
import org.xar.ck3.control.application.action.CompositeExecution;
import org.xar.ck3.control.application.action.GuardEvidence;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.advance.LifeAdvanceComposite;
import org.xar.ck3.control.application.planning.PlanTrace;
import org.xar.ck3.control.application.session.BatchReport;
import org.xar.ck3.control.application.session.SessionClock;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.application.session.SessionPorts.TurnFacts;
import static org.junit.jupiter.api.Assertions.*;

/** Actual receipt DATA and source-derived typed negatives; no Controller/native recovery is claimed. */
final class RootOrdinaryWorkerWallRecoveryTest {
    private static final Instant ORIGINAL_DEADLINE = Instant.parse("2026-11-01T04:27:05.512190600Z");
    private static final Clock FRESH_CLOCK = Clock.fixed(Instant.parse("2026-11-01T04:30:00Z"), ZoneOffset.UTC);
    private static final String BODY_SHA = "851d0b1284beee234ad567d8ff015c77d377287713d1c445e247b3d401e0cf67";
    private static final String RESOURCE_SHA = "4d934ced64b341aa481e8bd0fcece0e4c18375c2965d208b67f4d8f2c7b30709";

    @Test void expiredOriginalAppliedLifeRemainsAdmissibleWithoutChangingItsBody() throws Exception {
        var receipt = heldReceipt();
        byte[] originalCommand = ActionCodec.encodeCommand(receipt.command());
        assertEquals(ORIGINAL_DEADLINE, receipt.command().deadline());
        assertEquals(BODY_SHA, receipt.bodySha256());
        assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED, receipt.outcome());
        assertTrue(receipt.visibleGameplay());
        assertTrue(receipt.eligibleAdvance());
        assertTrue(FRESH_CLOCK.instant().isAfter(receipt.command().deadline()));
        Instant separateOperationDeadline = FRESH_CLOCK.instant().plus(Duration.ofMinutes(20));
        assertTrue(separateOperationDeadline.isAfter(FRESH_CLOCK.instant()));

        var report = report(BatchReport.Terminal.WALL_TIMEOUT, owner(receipt), List.of(receipt));
        assertSame(receipt, RootOrdinaryWorkerLoop.appliedLifeAtWall(report).orElseThrow());
        assertArrayEquals(originalCommand, ActionCodec.encodeCommand(receipt.command()));
        assertEquals(BODY_SHA, receipt.bodySha256());
        assertEquals(ORIGINAL_DEADLINE, receipt.command().deadline());
        assertNotEquals(separateOperationDeadline, receipt.command().deadline());
    }

    @Test void nonWallAndForeignReportOwnersAreNotAdmitted() throws Exception {
        var receipt = heldReceipt();
        var owner = owner(receipt);
        for (var terminal : List.of(BatchReport.Terminal.TURN_BOUND, BatchReport.Terminal.ACTION_UNKNOWN,
                BatchReport.Terminal.WRITER_UNKNOWN)) {
            assertTrue(RootOrdinaryWorkerLoop.appliedLifeAtWall(report(terminal, owner, List.of(receipt))).isEmpty(), terminal.name());
        }
        for (var foreign : List.of(new SessionIdentity("wall-other-machine", owner.game(), owner.sessionId()),
                new SessionIdentity(owner.machineId(), owner.game(), "wall-other-session"))) {
            assertTrue(RootOrdinaryWorkerLoop.appliedLifeAtWall(
                    report(BatchReport.Terminal.WALL_TIMEOUT, foreign, List.of(receipt))).isEmpty());
        }
    }

    @Test void anyReportedUnknownRefusesRecoveryOfAnEarlierAppliedLife() throws Exception {
        var applied = heldReceipt();
        var command = derivedCommand(applied.command(), "wall-data-unknown-parent", applied.command().operation());
        var unknown = new ActionReceipt(1, applied.sequence() + 1, command, ActionCodec.bodySha256(command),
                new ActionState.Unknown(Optional.empty(), Optional.empty(), "source-derived unresolved DATA", List.of()));
        assertFalse(unknown.settled());
        assertEquals(ActionReceipt.Outcome.UNRESOLVED, unknown.outcome());
        assertNotEquals(applied.command().actionId(), unknown.command().actionId());
        assertTrue(RootOrdinaryWorkerLoop.appliedLifeAtWall(
                report(BatchReport.Terminal.WALL_TIMEOUT, owner(applied), List.of(applied, unknown))).isEmpty());
    }

    @Test void laterRejectedParentCannotFallBackToEarlierAppliedLife() throws Exception {
        var applied = heldReceipt();
        var command = derivedCommand(applied.command(), "wall-data-rejected-parent", applied.command().operation());
        var execution = ((ActionState.CompositeSettled) applied.state()).execution();
        var rejected = new ActionReceipt(1, applied.sequence() + 1, command, ActionCodec.bodySha256(command),
                new ActionState.CompositeSettled(execution,
                        new ActionState.CompositeRejected("source-derived rejection DATA", execution.children())));
        assertTrue(rejected.settled());
        assertEquals(ActionReceipt.Outcome.REJECTED_CONFIRMED, rejected.outcome());
        assertFalse(rejected.eligibleAdvance());
        assertNotEquals(applied.command().actionId(), rejected.command().actionId());
        assertTrue(RootOrdinaryWorkerLoop.appliedLifeAtWall(
                report(BatchReport.Terminal.WALL_TIMEOUT, owner(applied), List.of(applied, rejected))).isEmpty());
    }

    @Test void laterAppliedNonLifeDataIsNotMistakenForThePendingLifeParent() throws Exception {
        var applied = heldReceipt();
        var command = derivedCommand(applied.command(), "wall-data-other-parent", new OperationKey("wall-data-other-gameplay"));
        var old = ((ActionState.CompositeSettled) applied.state()).execution();
        var oldGuard = old.guard();
        var guard = new GuardEvidence(command.origin(), command.source(), command.sessionId(),
                oldGuard.connectionGeneration(), command.operation(), oldGuard.nativeEvidence(), oldGuard.capabilityEvidence(),
                oldGuard.authorityId(), oldGuard.observedAt(), oldGuard.validUntil(), oldGuard.supportingEvidence());
        // These are valid DTO constructor relationships, never a canonical/native proof for a new operation.
        var execution = new CompositeExecution("wall-data-other-handler", old.startedAt(), guard, List.of());
        var other = new ActionReceipt(1, applied.sequence() + 1, command, ActionCodec.bodySha256(command),
                new ActionState.CompositeSettled(execution, applied.applied().orElseThrow()));
        assertEquals(ActionReceipt.Outcome.APPLIED_CONFIRMED, other.outcome());
        assertTrue(other.settled());
        assertTrue(other.visibleGameplay());
        assertTrue(other.eligibleAdvance());
        assertFalse(LifeAdvanceComposite.accepts(other.command().operation().value()));
        assertEquals(command.operation(), execution.guard().operation());
        assertTrue(RootOrdinaryWorkerLoop.appliedLifeAtWall(
                report(BatchReport.Terminal.WALL_TIMEOUT, owner(applied), List.of(applied, other))).isEmpty());
    }

    @Test void operatorStopBeforeEntryNeverResolvesSessionOrPublishesReport() throws Exception {
        var accesses = new AtomicInteger();
        var publications = new AtomicInteger();
        var control = new RootOrdinaryWorkerLoop.Control() {
            @Override public boolean stopRequested() { return true; }
            @Override public void onBatchCompleted(BatchReport report, long nextBatchSequence) { publications.incrementAndGet(); }
        };
        RootOrdinaryWorkerLoop.BatchAccess access = () -> {
            accesses.incrementAndGet();
            throw new AssertionError("stop must precede session resolution, batch and recovery callbacks");
        };
        var configuration = new RootOrdinaryWorkerLoop.Configuration("wall-data-worker", 2, Duration.ofMinutes(20),
                Duration.ofSeconds(60), Duration.ofMillis(50), 3);
        var result = new RootOrdinaryWorkerLoop(configuration, control, FRESH_CLOCK).run(access, 81);
        assertEquals(RootOrdinaryWorkerLoop.StopReason.OPERATOR_STOP, result.stopReason());
        assertEquals(81, result.nextBatchSequence());
        assertTrue(result.lastReport().isEmpty());
        assertEquals(0, accesses.get());
        assertEquals(0, publications.get());
    }

    private static ActionReceipt heldReceipt() throws IOException {
        byte[] raw;
        try (var stream = RootOrdinaryWorkerWallRecoveryTest.class.getResourceAsStream("wall-applied-life780.json")) {
            assertNotNull(stream, "exact held receipt classpath resource");
            raw = stream.readAllBytes();
        }
        assertEquals(9206, raw.length);
        assertEquals(RESOURCE_SHA, ActionCodec.sha256(raw));
        var archiveCalls = new AtomicInteger();
        var forbidden = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                new Class<?>[] {ActionPorts.OutcomeArchive.class}, (proxy, method, arguments) -> {
                    archiveCalls.incrementAndGet();
                    throw new AssertionError("inline held receipt must not access archive: " + method.getName());
                });
        var result = ActionReceiptCodec.decodeReceipt(raw, forbidden);
        assertEquals(0, archiveCalls.get());
        assertEquals(BODY_SHA, result.bodySha256());
        return result;
    }

    private static SessionIdentity owner(ActionReceipt receipt) {
        return new SessionIdentity(receipt.command().origin().machineId(), receipt.command().origin().game(), receipt.command().sessionId());
    }

    private static ActionCommand derivedCommand(ActionCommand original, String actionId, OperationKey operation) {
        return new ActionCommand(actionId, original.origin(), original.source(), original.sessionId(), operation,
                original.arguments(), original.expectation(), original.claims(), original.deadline());
    }

    private static BatchReport report(BatchReport.Terminal terminal, SessionIdentity owner, List<ActionReceipt> receipts) {
        var turns = new java.util.ArrayList<BatchReport.Turn>();
        for (var receipt : receipts) {
            var plan = new PlanTrace(receipt.command().before(), List.of(), Optional.empty());
            var evidence = receipt.applied().map(effect -> List.of(effect.observation().originalEvidence())).orElseGet(List::of);
            turns.add(new BatchReport.Turn(turns.size() + 1, receipt.command().before(), plan, receipt,
                    new TurnFacts(receipt.visibleGameplay(), receipt.eligibleAdvance(), evidence)));
        }
        var began = new SessionClock.Tick(0, FRESH_CLOCK.instant().minus(Duration.ofMinutes(20)));
        var ended = new SessionClock.Tick(Duration.ofMinutes(20).toNanos(), FRESH_CLOCK.instant());
        return new BatchReport(owner, "resume85_vanilla_ordinary01-80", terminal, "wall recovery DATA fixture", began, ended,
                List.of(), turns, List.of(), List.of(), List.of(), List.of(), Optional.empty(), Optional.empty(), Optional.empty(),
                Optional.empty(), Optional.empty(), 0, 1, true, List.of(), List.of(), List.of());
    }
}
