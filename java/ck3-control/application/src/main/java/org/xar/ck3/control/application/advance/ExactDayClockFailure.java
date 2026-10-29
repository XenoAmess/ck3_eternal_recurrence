package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.reconciliation.LateOutcome.Status;

/** Typed original pre-normal-Status failure. It never represents an observed stop or replay permission. */
public final class ExactDayClockFailure {
    public static final String MESSAGE = "exact-day native clock did not stop the map";
    private ExactDayClockFailure() { }
    public record CleanupTrace(Optional<AdvanceObservationPort.Frame> beforePause,
            Optional<ClockStatusRead.Observation> status, Optional<String> error) {
        public CleanupTrace { Objects.requireNonNull(beforePause); Objects.requireNonNull(status); Objects.requireNonNull(error); }
        public static CleanupTrace empty() { return new CleanupTrace(Optional.empty(),Optional.empty(),Optional.empty()); }
    }
    public static final class StopNotObserved extends IllegalStateException {
        private static final long serialVersionUID = 1L;
        // In-process failure context; durable evidence uses the existing JSON publisher.
        @SuppressWarnings("serial")
        private final ActionCommand parent;
        @SuppressWarnings("serial")
        private final AdvancePlan plan;
        @SuppressWarnings("serial")
        private final AdvanceObservationPort.Frame starting, lastWait;
        @SuppressWarnings("serial")
        private final Status armed;
        private final int actionStart;
        @SuppressWarnings("serial")
        private final List<ActionReceipt> beforeCleanup;
        StopNotObserved(ActionCommand parent, AdvancePlan plan, AdvanceObservationPort.Frame starting,
                AdvanceObservationPort.Frame lastWait, Status armed, int actionStart, List<ActionReceipt> beforeCleanup) {
            super(MESSAGE); this.parent=Objects.requireNonNull(parent); this.plan=Objects.requireNonNull(plan);
            this.starting=Objects.requireNonNull(starting); this.lastWait=Objects.requireNonNull(lastWait);
            this.armed=Objects.requireNonNull(armed); this.beforeCleanup=List.copyOf(beforeCleanup); this.actionStart=actionStart;
            require(LifeAdvanceComposite.accepts(parent.operation().value()) && plan.equals(AdvancePlan.decode(parent))
                    && plan.exactOneDay() && plan.clockMode()==AdvancePlan.ClockMode.EXACT_SENTINEL && plan.dailyWatch().isEmpty()
                    && parent.expected().observerSchema().equals(AdvancePlan.OBSERVER) && parent.expected().values().equals(plan.expected())
                    && starting.identity().equals(parent.before()) && actionStart>=0 && beforeCleanup.size()<=256,
                    "exact-day stop failure requires the original non-Watch exact sentinel Life plan");
            AdvanceWait.binding(parent,starting,lastWait);
            require(!AdvancePolicy.truth(lastWait.semantic(),"paused")
                    && AdvanceProgress.newModal(lastWait.semantic(),starting.identity(),Optional.of(starting.semantic())).isEmpty(),
                    "exact-day stop failure is only a real running pre-normal-Status frame without modal pause");
            AdvanceClock.validateArm(armed,plan); AdvanceClockArchivedReplay.verifyChildBindings(parent,this.beforeCleanup);
            List<ActionReceipt> arms=this.beforeCleanup.stream().filter(child -> child.command().operation().value().equals(plan.armStep())).toList();
            require(arms.size()==1 && arms.getFirst().outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED
                    && armed.equals(AdvancePrimitives.acknowledgedSentinel(arms.getFirst().ack().orElseThrow(),plan.armStep())),
                    "exact-day failure arm differs from its actual original child ACK");
            long resumes=this.beforeCleanup.stream().filter(child -> child.command().operation().value().equals("resume-map")
                    && child.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED).count();
            require(resumes==1 && this.beforeCleanup.stream().allMatch(child -> {
                String step=child.command().operation().value(); return step.equals(plan.armStep()) || step.equals("resume-map") || step.equals("set-speed-"+plan.speed());
            }),"pre-normal-Status exact-day failure must retain its original arm/single resume and no cleanup controls");
            ActionReceipt resume=this.beforeCleanup.stream().filter(child -> child.command().operation().value().equals("resume-map")).findFirst().orElseThrow();
            require(this.beforeCleanup.indexOf(arms.getFirst())<this.beforeCleanup.indexOf(resume)
                    && resume.state() instanceof ActionState.Settled settled && settled.settlement() instanceof ActionState.Applied,
                    "exact-day failure lost its original arm-before-resume actual effect");
            var resumed=((ActionState.Applied)((ActionState.Settled)resume.state()).settlement()).observation();
            require(!lastWait.observedAt().isBefore(resumed.observedAt())
                    && lastWait.identity().frame().revision().compareTo(resumed.after().frame().revision())>=0
                    && lastWait.identity().frame().identity().nativeRevision().compareTo(resumed.after().frame().identity().nativeRevision())>=0,
                    "exact-day last wait frame predates the actual original resume effect");
        }
        public ActionCommand parent(){return parent;} public AdvancePlan plan(){return plan;}
        public AdvanceObservationPort.Frame starting(){return starting;} public AdvanceObservationPort.Frame lastWait(){return lastWait;}
        public Status armed(){return armed;} public int actionStart(){return actionStart;}
        public List<ActionReceipt> beforeCleanup(){return beforeCleanup;}
        public int cleanupStart(){return Math.addExact(actionStart,beforeCleanup.size());}
    }
}
