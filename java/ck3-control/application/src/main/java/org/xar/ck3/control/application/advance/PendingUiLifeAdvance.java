package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.Arrays;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.history.DriverSurvivingHistory;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;

/** Private DATA access for one source-approved successor UI date child. This is neither Ready nor action permission.
 * The registered continuation source and canonical coordinator independently approve the original parent,
 * exact Life child, each primitive, once intent, actual Close/clearance and Native preparation originals.
 */
public final class PendingUiLifeAdvance {
    private PendingUiLifeAdvance() { }
    public static final String POLICY = "successor_ui_once_date_proof";

    @FunctionalInterface public interface Work<T> { T run(Current actual) throws IOException; }
    @FunctionalInterface public interface Work0<T> { T run() throws IOException; }
    @FunctionalInterface public interface SessionAccess { Session current() throws IOException; }

    /** Implementing this interface does not register a continuation or mint a private permission. */
    public interface Source {
        ActionCommand originalParent();
        void requireCurrent(Session same) throws IOException;
        <T> T withCurrent(Session same, Instant deadline, Work<T> work) throws IOException;
        <T> T withNext(Session same, ObservationIdentity after, Instant deadline, Work<T> work) throws IOException;
        NativeRequest preparePreclock(Session same, ActionCommand resumeChild, String requestId, NativeRequest base) throws IOException;
    }

    /** Source-owned physical Native/complete Driver join, plus actual archived predecessor originals.
     * Constructors validate DATA only. Root's private source must reload/verify these originals and its
     * genuine pending publication/cause against the same current writer and owning physical lease.
     * Running frames retain paused=false; only preparation/readiness and Status admission require pause.
     */
    public record Current(AdvanceObservationPort.Frame originalFrame, DriverSnapshotFacts.Known actualKnown,
            ExactRef originalDriver, ExactRef originalHistoryBasis, ExactRef originalPendingPublication,
            ExactRef originalCloseReceipt, ExactRef materialClearance, ActionReceipt actualCloseReceipt,
            Set<OperationKey> actualActionSteps, Set<String> actualBridgeCapabilities) {
        public Current {
            Objects.requireNonNull(originalFrame); Objects.requireNonNull(actualKnown); Objects.requireNonNull(actualCloseReceipt);
            for (ExactRef ref : java.util.List.of(originalDriver, originalHistoryBasis, originalPendingPublication,
                    originalCloseReceipt, materialClearance)) require(ref.bytes() > 0, "actual pending date originals required");
            actualActionSteps = Set.copyOf(actualActionSteps); actualBridgeCapabilities = Set.copyOf(actualBridgeCapabilities);
            actualBridgeCapabilities.forEach(org.xar.ck3.control.contracts.StrictJson::text);
            var known = actualKnown; var frame = originalFrame.identity(); var driver = known.driver();
            require(known.stamp().game().equals(frame.game()) && known.stamp().episodeRunId().equals(frame.frame().episodeRunId())
                    && driver.session().actorId().equals(frame.frame().identity().player())
                    && driver.session().episodeRunId().equals(frame.frame().episodeRunId())
                    && driver.session().bridgePid() == frame.game().pid()
                    && originalHistoryBasis.equals(known.originalHistoryBasis())
                    && originalDriver.sha256().equals(known.stamp().driverSha256())
                    && originalDriver.bytes() == driver.encode().length,
                    "pending date DATA crossed its actual complete Driver/Game/actor/run/history original");
            require(actualCloseReceipt.state() instanceof ActionState.Settled closed
                    && closed.settlement() instanceof ActionState.ControlApplied
                    && actualCloseReceipt.command().source().equals(originalFrame.source())
                    && actualCloseReceipt.command().sessionId().equals(originalFrame.sessionId())
                    && actualCloseReceipt.command().origin().game().equals(frame.game()),
                    "pending date needs its actual canonical independent Close control, not an ACK");
        }
    }

    /** One dynamic scope is shared by the existing infrastructure, same Life composite and command producer. */
    public static final class Scope {
        private static final class Held {
            private final Source source; private final Session session;
            // Immutable captured DATA only; never a Root SnapshotLease or a replacement Ready.
            private Current captured;
            private Held(Source source, Session session) { this.source = source; this.session = session; }
            private Source source() { return source; }
            private Session session() { return session; }
        }
        private final SessionAccess sessions;
        private final ThreadLocal<Held> active = new ThreadLocal<>();
        public Scope(SessionAccess actualBorrowedSession) { sessions = Objects.requireNonNull(actualBorrowedSession); }
        public boolean active() { return active.get() != null; }

        /** Holds only private source custody. Every physical callback closes before a Native child submits. */
        public <T> T within(Source actual, Work0<T> work) throws IOException {
            Objects.requireNonNull(actual); Objects.requireNonNull(work);
            require(active.get() == null, "nested or escaped pending date source scope");
            Session same = Objects.requireNonNull(sessions.current()); actual.requireCurrent(same);
            ActionCommand ancestor = Objects.requireNonNull(actual.originalParent());
            require(ancestor.origin() instanceof CommandOrigin.LifecycleTerminal
                    && ancestor.lifecycleExpected().operation() == LifecycleExpectedPostcondition.Operation.CONTINUE_SUCCESSOR,
                    "pending date source is not its original successor Continue ancestor");
            Held entered = new Held(actual, same); active.set(entered);
            try { return work.run(); } finally { entered.captured = null; active.remove(); }
        }

        public AdvanceObservationPort observations(AdvanceObservationPort actualOrdinary) {
            Objects.requireNonNull(actualOrdinary);
            return new AdvanceObservationPort() {
                @Override public Frame current(ActionCommand command, Instant deadline) {
                    Held held = active.get(); if (held == null) return actualOrdinary.current(command, deadline);
                    try {
                        held.captured = null; Session same = held(held);
                        return held.source().withCurrent(same, deadline, value -> {
                            Frame result = checkedFrame(held, command, value); held.captured = value; return result;
                        });
                    } catch (IOException failure) { held.captured = null; throw new UncheckedIOException("actual pending date current unavailable", failure); }
                    catch (RuntimeException | Error failure) { held.captured = null; throw failure; }
                }
                @Override public <T> T withClockControlBasis(ActionCommand command, Instant deadline,
                        java.util.function.Function<Frame,T> work) {
                    Objects.requireNonNull(work);
                    if (active.get() == null) return actualOrdinary.withClockControlBasis(command,deadline,work);
                    return work.apply(current(command,deadline));
                }
                @Override public Frame next(ActionCommand command, ObservationIdentity after, Instant deadline) {
                    Held held = active.get(); if (held == null) return actualOrdinary.next(command, after, deadline);
                    try {
                        held.captured = null; Session same = held(held);
                        return held.source().withNext(same, after, deadline, value -> {
                            Frame result = checkedFrame(held, command, value);
                            require(result.identity().game().equals(after.game())
                                    && result.identity().frame().episodeRunId().equals(after.frame().episodeRunId())
                                    && result.identity().frame().identity().player().equals(after.frame().identity().player())
                                    && result.identity().frame().revision().compareTo(after.frame().revision()) >= 0
                                    && result.identity().frame().identity().nativeRevision().compareTo(after.frame().identity().nativeRevision()) >= 0,
                                    "pending date next left its actual same actor/run or regressed");
                            held.captured = value; return result;
                        });
                    } catch (IOException failure) { held.captured = null; throw new UncheckedIOException("actual pending date next unavailable", failure); }
                    catch (RuntimeException | Error failure) { held.captured = null; throw failure; }
                }
            };
        }

        /** Pure one-use policy consumer of the last actual observation capture, with live source/writer custody.
         * No physical recapture and no lease escapes; canonical Root guards still revalidate before dispatch.
         */
        public AdvanceReadiness.Port readiness(AdvanceReadiness.Port actualOrdinary) {
            Objects.requireNonNull(actualOrdinary);
            return (command, frame) -> {
                Held held = active.get(); if (held == null) return actualOrdinary.inspect(command, frame);
                try {
                    Current value = held.captured; held.captured = null;
                    held(held);
                    require(value != null, "pending date policy has no unconsumed same-source current capture");
                    require(checkedFrame(held, command, value).equals(frame), "pending date policy crossed its actual captured Native/Driver frame");
                    requirePurpose(command);
                    // Consume exactly the DATA captured by observations.current/next. Another withCurrent
                    // would physically observe again and could change snapshotId/observedAt before validation.
                    return facts(command, value);
                } catch (IOException failure) { throw new UncheckedIOException("actual pending date readiness unavailable", failure); }
            };
        }

        /** Called only by the real canonical-session primitive producer before its durable intent. */
        public NativeRequest prepare(Session same, ActionCommand command, String requestId, NativeRequest base) throws IOException {
            Objects.requireNonNull(same); Objects.requireNonNull(command); Objects.requireNonNull(base);
            Held held = active.get(); if (held == null) return base;
            held.captured = null; // A Native child cannot carry the former policy capture across its intent.
            require(same == held(held), "pending date preparation escaped its actual writer session");
            require(AdvancePrimitives.supports(command.operation()), "pending date permits only its canonical finite clock primitives");
            if (!command.operation().value().equals("resume-map")) return base;
            org.xar.ck3.control.contracts.StrictJson.text(requestId);
            NativeRequest original = held.source().preparePreclock(same, command, requestId, base);
            held.source().requireCurrent(same);
            require(original.step().equals(base.step()) && original.requiredCapability().equals(base.requiredCapability())
                    && Arrays.equals(original.additionalFields().bytes(), base.additionalFields().bytes())
                    && original.preparationEvidence().containsAll(base.preparationEvidence())
                    && !original.preparationEvidence().isEmpty(),
                    "pending resume lost actual preclock originals or changed its original Native wire");
            return original;
        }

        /** Actual source callback supplies all immutable policy inputs; no ordinary PlanningRequest/Ready is created. */
        public <T> T capture(Source source, Instant deadline, Work<T> work) throws IOException {
            Objects.requireNonNull(source); Objects.requireNonNull(deadline); Objects.requireNonNull(work);
            Session same = Objects.requireNonNull(sessions.current()); source.requireCurrent(same);
            return source.withCurrent(same, deadline, value -> { source.requireCurrent(same); return work.run(value); });
        }

        private Session held(Held held) throws IOException {
            require(active.get() == held && sessions.current() == held.session(), "pending date source or actual writer session escaped");
            held.source().requireCurrent(held.session()); return held.session();
        }
        private static AdvanceObservationPort.Frame checkedFrame(Held held, ActionCommand command, Current actual) throws IOException {
            held.source().requireCurrent(held.session());
            var frame = actual.originalFrame(); var ancestor = held.source().originalParent();
            require((command.operation().value().equals("life-advance") || AdvancePrimitives.supports(command.operation()))
                    && command.origin() instanceof CommandOrigin.Gameplay
                    && command.source().equals(frame.source()) && command.sessionId().equals(frame.sessionId())
                    && ancestor.source().equals(frame.source()) && ancestor.sessionId().equals(frame.sessionId())
                    && ancestor.origin().game().equals(frame.identity().game())
                    && command.before().game().equals(frame.identity().game())
                    && command.before().frame().episodeRunId().equals(frame.identity().frame().episodeRunId())
                    && command.before().frame().identity().player().equals(frame.identity().frame().identity().player())
                    && frame.identity().frame().revision().compareTo(command.before().frame().revision()) >= 0
                    && frame.identity().frame().identity().nativeRevision().compareTo(command.before().frame().identity().nativeRevision()) >= 0,
                    "pending date left its actual source-approved finite clock Game/session/actor/run");
            return frame;
        }
    }

    public static AdvanceReadiness.Facts facts(ActionCommand exactChild, Current actual) {
        Objects.requireNonNull(exactChild); Objects.requireNonNull(actual);
        // One day is the minimum existing Crown bound. Optional ordinary war-watch scheduling is not this purpose.
        return AdvanceHistory.verifiedFacts(exactChild, actual.originalFrame(), DriverSurvivingHistory.rows(actual.actualKnown().driver()),
                actual.actualActionSteps(), actual.actualBridgeCapabilities(), 1, false, actual.originalDriver());
    }
    public static void requirePurpose(ActionCommand command) {
        require(command.operation().value().equals("life-advance"), "private date child must be the exact registered Life operation");
        AdvancePlan plan = AdvancePlan.decode(command);
        require(plan.policy().equals(POLICY) && plan.exactOneDay() && plan.horizonDays() == 1 && plan.speed() == 1
                && plan.clockMode() == AdvancePlan.ClockMode.EXACT_SENTINEL && plan.campaignDeadline().isEmpty() && plan.dailyWatch().isEmpty()
                && plan.targetDateRaw().equals(plan.startingDateRaw().add(AdvancePlan.DAY)),
                "private pending date cannot widen its once one-day Native sentinel purpose");
    }
}
