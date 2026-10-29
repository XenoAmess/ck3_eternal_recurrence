package org.xar.ck3.control.g2.m7.schedule;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.M7OrdinaryPlanConsumer;
import org.xar.ck3.control.g2.m7.OrdinaryCampaignGoal;
import org.xar.ck3.control.planning.campaigncadence.CampaignCalendar;

/** Ordinary full-planner consumption of the retained goal and its fixed founding clock. */
public final class OrdinaryCampaignSchedule {
    public static final BigInteger MAX_CLOCK_TARGET = BigInteger.ONE.shiftLeft(4096).subtract(BigInteger.ONE);
    private OrdinaryCampaignSchedule() { }

    /** Only the already reconciled goal changes at succession; the founding calendar stays exact. */
    public record State(OrdinaryCampaignGoal.Goal goal, Optional<CampaignDeadline.Configuration> deadline) {
        public State {
            Objects.requireNonNull(goal, "goal"); Objects.requireNonNull(deadline, "deadline");
            deadline.ifPresent(configuration -> {
                // Goal lineage and the independently configured founding clock use different ID namespaces.
                StrictJson.require(configuration.equals(CampaignDeadline.configure(configuration.founding(),
                        OrdinaryCampaignSchedule::calendar, Optional.empty())),
                        "ordinary schedule requires the shared complete founding calendar");
            });
        }
    }

    public enum ClockStatus {
        NO_CLOCK_REQUEST("no_clock_request"), NO_DEADLINE("no_deadline"), ADVANCE("advance"),
        ENDPOINT_REACHED("endpoint_reached"), ENDPOINT_OVERSHOT("endpoint_overshot");
        private final String wire;
        ClockStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }

    /** The full planner still selects the step. This consumer supplies only its bounded clock target. */
    public record Plan(State state, M7OrdinaryPlanConsumer.Consumed ordinaryPlan,
            Optional<BigInteger> requestedClockTargetRaw, Optional<CampaignDeadline.Cap> clockDeadline) {
        public Plan {
            Objects.requireNonNull(state, "state"); Objects.requireNonNull(ordinaryPlan, "ordinaryPlan");
            Objects.requireNonNull(requestedClockTargetRaw, "requestedClockTargetRaw");
            Objects.requireNonNull(clockDeadline, "clockDeadline");
            StrictJson.require(state.goal().equals(ordinaryPlan.observation().goal()),
                    "ordinary scheduling consumes the exact persisted current-ruler goal");
            requestedClockTargetRaw.ifPresent(target -> {
                BigInteger current = BigInteger.valueOf(ordinaryPlan.observation().dateRaw());
                StrictJson.require(target.compareTo(current) > 0 && target.compareTo(MAX_CLOCK_TARGET) <= 0
                        && target.subtract(current).mod(BigInteger.valueOf(24)).signum() == 0,
                        "planner clock proposal must be a forward whole-day target");
            });
            StrictJson.require(clockDeadline.equals(cap(state, ordinaryPlan, requestedClockTargetRaw)),
                    "persisted ordinary deadline must equal the actual shared clock producer");
        }
        public ClockStatus clockStatus() {
            if (requestedClockTargetRaw.isEmpty()) { return ClockStatus.NO_CLOCK_REQUEST; }
            if (clockDeadline.isEmpty()) { return ClockStatus.NO_DEADLINE; }
            return switch (clockDeadline.orElseThrow().status()) {
                case ADVANCE -> ClockStatus.ADVANCE;
                case ENDPOINT_REACHED -> ClockStatus.ENDPOINT_REACHED;
                case ENDPOINT_OVERSHOT -> ClockStatus.ENDPOINT_OVERSHOT;
            };
        }
        /** Endpoint branches have no new clock target; this does not submit or settle a command. */
        public Optional<BigInteger> effectiveClockTargetRaw() {
            if (clockDeadline.isEmpty()) { return requestedClockTargetRaw; }
            CampaignDeadline.Cap value = clockDeadline.orElseThrow();
            return value.status() == CampaignDeadline.Status.ADVANCE ? Optional.of(value.targetDateRaw()) : Optional.empty();
        }
        public boolean gameActionsSubmitted() { return false; }
        public boolean coldAuthorityGranted() { return false; }
        public boolean replayAuthorized() { return false; }
        public int savedDayCredit() { return 0; }
    }

    public static State continueAfterReconciliation(State state, OrdinaryCampaignGoal.Reconciliation reconciliation) {
        Objects.requireNonNull(state, "state");
        return new State(OrdinaryCampaignGoal.continueGoal(state.goal(), reconciliation), state.deadline());
    }

    public static Plan consume(State state, M7OrdinaryPlanConsumer.Consumed ordinaryPlan,
            Optional<BigInteger> requestedClockTargetRaw) {
        return new Plan(state, ordinaryPlan, requestedClockTargetRaw, cap(state, ordinaryPlan, requestedClockTargetRaw));
    }

    /** Shared adapter, with no duplicate CK3 calendar arithmetic in the schedule or admission layer. */
    public static CampaignDeadline.CalendarSchedule calendar(String startDate, int months) {
        return new CampaignDeadline.CalendarSchedule(CampaignCalendar.PROFILE, startDate,
                BigInteger.valueOf(CampaignCalendar.dateToRaw(startDate)),
                CampaignCalendar.monthBoundaries(startDate, months).stream()
                        .map(boundary -> BigInteger.valueOf(boundary.raw())).toList());
    }

    private static Optional<CampaignDeadline.Cap> cap(State state, M7OrdinaryPlanConsumer.Consumed plan,
            Optional<BigInteger> target) {
        Objects.requireNonNull(state, "state"); Objects.requireNonNull(plan, "plan"); Objects.requireNonNull(target, "target");
        return target.isEmpty() ? Optional.empty() : CampaignDeadline.deadline(state.deadline(),
                BigInteger.valueOf(plan.observation().dateRaw()), target.orElseThrow());
    }
}
