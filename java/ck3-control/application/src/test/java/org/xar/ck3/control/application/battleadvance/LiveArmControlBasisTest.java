package org.xar.ck3.control.application.battleadvance;

import static org.junit.jupiter.api.Assertions.*;

import java.math.BigInteger;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.advance.AdvanceObservationPort.Frame;
import org.xar.ck3.control.contracts.CrossJsDecimalUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.reconciliation.LateOutcome.Mode;
import org.xar.ck3.control.reconciliation.LateOutcome.State;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;
import org.xar.ck3.control.wave2.runtime.deadlinetransport.SentinelObservation;

/** Software ARM/STATUS packets. The retained basis is never a Native poststate or live permission. */
final class LiveArmControlBasisTest {
    private static final String ARM = "research-arm-tactical-daily-sentinel-v1-100-to-124-speed-3-mode-decision-a-1-0";

    @Test void realArmAndIndependentStatusUseTheForwardedBasisWithoutAnOrdinaryPublication() {
        var harness = new Harness();
        ActionCommand child = harness.child(ARM);
        ActionPorts.ControlObserved observed = assertInstanceOf(ActionPorts.ControlObserved.class,
                harness.primitives.observe(child, harness.attempt(child), harness.armAck(child)));
        assertEquals(1, harness.basisReads);
        assertEquals(0, harness.ordinaryReads);
        assertEquals(1, harness.statusReads);
        assertEquals(ClockStatusRead.STEP, observed.observation().read().request().operation().value());
        assertNotEquals("arm-request", observed.observation().read().requestId());
        assertEquals(harness.actual, ClockStatusRead.decode(observed.observation().read().original()));
        assertEquals(harness.basis.identity(), observed.observation().read().request().before());
    }

    @Test void aDifferentIndependentGenerationCannotBecomeControlApplied() {
        var harness = new Harness();
        harness.actual = status(ARM, "2");
        ActionCommand child = harness.child(ARM);
        assertThrows(IllegalArgumentException.class,
                () -> harness.primitives.observe(child, harness.attempt(child), harness.armAck(child)));
        assertEquals(1, harness.statusReads);
        assertEquals(1, harness.basisReads);
        assertEquals(0, harness.ordinaryReads);
    }

    @Test void unavailableIndependentStatusCannotUseAnOrdinaryFallbackOrTheArmAck() {
        var harness = new Harness();
        harness.unavailable = true;
        ActionCommand child = harness.child(ARM);
        IllegalStateException failure = assertThrows(IllegalStateException.class,
                () -> harness.primitives.observe(child, harness.attempt(child), harness.armAck(child)));
        assertTrue(failure.getMessage().contains("native clock status unavailable"));
        assertEquals(1, harness.statusReads);
        assertEquals(1, harness.basisReads);
        assertEquals(0, harness.ordinaryReads);
    }

    @Test void clockReachesItsSingleResumeAfterArmWithoutWaitingForAnOrdinaryPush() {
        var harness = new Harness();
        var plan = new AdvancePlan(BigInteger.valueOf(100), BigInteger.valueOf(124), 1, 3,
                "fixture_exact_sentinel", true, AdvancePlan.ClockMode.EXACT_SENTINEL, Optional.empty());
        harness.actual = status(plan.armStep(), "1");
        var completed = new ArrayList<ActionReceipt>();
        var submitted = new ArrayList<String>();
        CompositeActionPort.Children children = new CompositeActionPort.Children() {
            @Override public String nextActionId() { return "clock-child-" + completed.size(); }
            @Override public List<ActionReceipt> completed() { return List.copyOf(completed); }
            @Override public ActionReceipt submit(ActionCommand child) {
                assertFalse(harness.insideBasis, "a read lease cannot enclose a Native mutation");
                submitted.add(child.operation().value());
                if (child.operation().value().equals("resume-map")) throw new ResumeReached();
                assertEquals(plan.armStep(), child.operation().value());
                ActionState.Attempt attempt = harness.attempt(child);
                var ack = harness.armAck(child);
                var observed = assertInstanceOf(ActionPorts.ControlObserved.class,
                        harness.primitives.observe(child, attempt, ack));
                var receipt = new ActionReceipt(1, completed.size() + 1L, child, ActionCodec.bodySha256(child),
                        new ActionState.Settled(attempt, ack, observed.observation()));
                completed.add(receipt);
                return receipt;
            }
        };
        var clock = new AdvanceClock(harness.forwarded, harness.statuses,
                (command, frame) -> new AdvanceReadiness.Facts(frame.identity(), java.util.Set.of(
                        new OperationKey("set-speed-3"), new OperationKey("resume-map"), new OperationKey("pause-map")),
                        java.util.Set.of(ClockStatusRead.ARM_CAP, ClockStatusRead.STATUS_CAP, ClockStatusRead.CANCEL_CAP),
                        false, false, false, 45, BattleAdvanceFixture.REF),
                Clock.fixed(BattleAdvanceFixture.NOW, ZoneOffset.UTC), 4, Duration.ofSeconds(30), Duration.ofSeconds(120));
        assertThrows(ResumeReached.class, () -> clock.execute(harness.parent, children, harness.basis, plan));
        assertEquals(List.of(plan.armStep(), "resume-map"), submitted);
        assertEquals(3, harness.basisReads, "ARM STATUS, post-ARM basis and pre-resume basis are distinct calls");
        assertEquals(1, harness.statusReads);
        assertEquals(0, harness.ordinaryReads);
        assertFalse(harness.insideBasis);
    }

    private static final class ResumeReached extends RuntimeException {
        private static final long serialVersionUID = 1L;
    }

    private static Status status(String step, String generation) {
        var arm = AdvancePrimitives.armSpec(step);
        return new Status(State.ARMED, new CrossJsDecimalUInt64(generation), arm.startingDateRaw(), arm.targetDateRaw(),
                arm.startingDateRaw(), 0, arm.speed(), arm.mode().equals("decision") ? Mode.DECISION_EPOCH : Mode.TERMINAL_OR_SENTINEL,
                arm.armyIds().size(), 0, 0, 0, 0, List.of(), 0, -1, false, false, false, false);
    }

    private static NativeActionPort.AckReceived ack(String id, String step, Status status) {
        var result = StrictJson.object();
        result.put("step", step); result.put("accepted", true); result.put("status", "available");
        result.set("tactical_daily_sentinel", SentinelObservation.toJson(status));
        var frame = StrictJson.object();
        frame.put("type", "command_result"); frame.put("request_id", id); frame.put("ok", true); frame.set("result", result);
        byte[] packet = StrictJson.canonical(frame);
        return new NativeActionPort.AckReceived(id, true, Optional.of(new RawJson(StrictJson.canonical(result))),
                new RawJson(packet), packet);
    }

    private static final class Harness implements AdvanceObservationPort, PlanningReadPort {
        private final Frame basis = BattleAdvanceFixture.frame(1, 100, true, false);
        private final ActionCommand parent = BattleAdvanceFixture.parent();
        private Status actual = status(ARM, "1");
        private boolean insideBasis;
        private boolean unavailable;
        private int basisReads;
        private int ordinaryReads;
        private int statusReads;
        private final AdvanceObservationPort forwarded = new PendingUiLifeAdvance.Scope(() -> {
            throw new AssertionError("inactive pending source cannot acquire a session");
        }).observations(this);
        private final ClockStatusRead statuses = new ClockStatusRead(this, BattleAdvanceFixture.REF,
                new BattleAdvanceFixture().archiveForTest());
        private final AdvancePrimitives primitives = new AdvancePrimitives(forwarded, statuses,
                Clock.fixed(BattleAdvanceFixture.NOW, ZoneOffset.UTC), 4);

        @Override public Frame current(ActionCommand command, Instant deadline) {
            ordinaryReads++;
            throw new AssertionError("no ordinary publication follows this software ARM ACK");
        }
        @Override public Frame next(ActionCommand command, ObservationIdentity after, Instant deadline) {
            ordinaryReads++;
            throw new AssertionError("no ordinary publication follows this software ARM ACK");
        }
        // Also compiles against the original interface: baseline has no method to override.
        public <T> T withClockControlBasis(ActionCommand command, Instant deadline, Function<Frame,T> work) {
            assertFalse(insideBasis);
            basisReads++; insideBasis = true;
            try { return work.apply(basis); }
            finally { insideBasis = false; }
        }
        @Override public <T> PlanningReadResult<T> read(ReadContract<T> contract, PlanningReadRequest request) {
            statusReads++;
            assertTrue(insideBasis, "independent registered STATUS borrows the exact control-read basis scope");
            assertSame(statuses.contract(), contract);
            assertEquals(ClockStatusRead.STEP, request.operation().value());
            assertEquals(basis.identity(), request.before());
            assertEquals(basis.source(), request.source());
            assertEquals(basis.sessionId(), request.sessionId());
            if (unavailable) return new PlanningReadResult.Unavailable<>("software status unavailable", Optional.empty());
            String readId = "status-request-" + statusReads;
            var guard = new PlanningReadGuard(guard(request.before(), request.operation()), true, true, true, "c".repeat(64));
            var receipt = new PlanningReadReceipt(request, contract.contractId(), readId, guard, guard,
                    ack(readId, ClockStatusRead.STEP, actual));
            return new PlanningReadResult.Known<>(contract.decode(receipt), receipt, BattleAdvanceFixture.REF);
        }
        private GuardEvidence guard(ObservationIdentity before, OperationKey operation) {
            return new GuardEvidence(before, basis.source(), basis.sessionId(), BigInteger.ONE, operation,
                    BattleAdvanceFixture.REF, BattleAdvanceFixture.REF, "software-clock-read", BattleAdvanceFixture.NOW,
                    parent.deadline());
        }
        private ActionCommand child(String step) {
            return AdvancePrimitives.child(parent, basis, "arm-child", step, parent.deadline());
        }
        private ActionState.Attempt attempt(ActionCommand child) {
            return new ActionState.Attempt("arm-request", BattleAdvanceFixture.NOW,
                    guard(child.before(), child.operation()), AdvancePrimitives.prepareRequest(child));
        }
        private NativeActionPort.AckReceived armAck(ActionCommand child) {
            return ack("arm-request", child.operation().value(), status(child.operation().value(), "1"));
        }
    }
}
