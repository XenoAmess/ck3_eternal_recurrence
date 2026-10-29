package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.math.BigInteger;
import java.util.Optional;
import org.xar.ck3.control.admission.deadlinecredit.CampaignDeadline;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Pure full-frame selector and immutable rewrite. No native call, writer, wait or game credit. */
public final class AdvanceRewrite {
    private AdvanceRewrite() { }
    public static ActionCommand exactDay(PlanningRequest request, ActionCommand original) {
        return rewrite(request, original, "life-advance-one-day", Optional.empty());
    }
    public static ActionCommand rewrite(PlanningRequest request, ActionCommand original, String effectiveStep, CampaignDeadline.Cap cap) {
        return rewrite(request, original, effectiveStep, Optional.of(cap));
    }
    public static ActionCommand rewrite(PlanningRequest request, ActionCommand original, String effectiveStep, Optional<CampaignDeadline.Cap> cap) {
        return rewriteBound(request, original, effectiveStep, cap, 45);
    }
    /** The real provider supplies its persisted same-source Crown retry bound, never draft detail. */
    public static ActionCommand rewriteBound(PlanningRequest request, ActionCommand original, String effectiveStep,
            Optional<CampaignDeadline.Cap> cap, int crownRetryMaximumDays) {
        return rewriteBound(request,original,effectiveStep,cap,crownRetryMaximumDays,Optional.empty());
    }
    public static ActionCommand rewriteBound(PlanningRequest request, ActionCommand original, String effectiveStep,
            Optional<CampaignDeadline.Cap> cap, AdvanceReadiness.Facts actual) {
        require(actual.observed().equals(request.before()), "actual retry/watch facts crossed the planning frame");
        return rewriteBound(request,original,effectiveStep,cap,actual.crownRetryMaximumDays(),Optional.of(actual));
    }
    private static ActionCommand rewriteBound(PlanningRequest request, ActionCommand original, String effectiveStep,
            Optional<CampaignDeadline.Cap> cap, int crownRetryMaximumDays, Optional<AdvanceReadiness.Facts> actual) {
        require(crownRetryMaximumDays >= 1 && crownRetryMaximumDays <= 45, "actual Crown retry horizon required");
        require(original.before().equals(request.before()) && original.source().equals(request.source())
                && original.sessionId().equals(request.sessionId()) && !original.deadline().isAfter(request.deadline()), "advance rewrite crossed planning identity");
        require(effectiveStep.equals("life-advance") || effectiveStep.equals("life-advance-one-day"), "life rewrite requires its original composite operation");
        AdvancePolicy.Choice choice = actual.map(value -> AdvancePolicy.select(request,effectiveStep,value)).orElseGet(() -> AdvancePolicy.select(request,effectiveStep));
        BigInteger start = request.before().frame().identity().dateRaw();
        BigInteger horizon = start.add(AdvancePlan.DAY.multiply(BigInteger.valueOf(Math.min(choice.horizonDays(), crownRetryMaximumDays))));
        var maximum = original.arguments().get("maximum_target_date_raw");
        if (maximum != null) {
            require(maximum instanceof OpportunityJson.IntegerValue, "advance maximum must be a strict integer JSON field");
            BigInteger bound = ((OpportunityJson.IntegerValue)maximum).value();
            require(bound.compareTo(start) > 0 && bound.subtract(start).mod(AdvancePlan.DAY).signum() == 0,
                    "advance maximum must be a forward whole-day target from the actual starting date");
            horizon = horizon.min(bound);
        }
        final BigInteger requested = horizon;
        Optional<CampaignDeadline.Cap> actualCap = cap.map(value -> {
            require(value.status() == CampaignDeadline.Status.ADVANCE && value.startingDateRaw().equals(start), "endpoint or stale campaign frame cannot become an advance");
            // M7 passes current+1 only to locate the next boundary. Retain the real full-frame horizon.
            return new CampaignDeadline.Cap(value.campaignId(), value.calendarProfile(), start, requested,
                    value.boundaryDateRaw(), value.endpointDateRaw(), requested.min(value.boundaryDateRaw()), value.status());
        });
        BigInteger target = actualCap.map(CampaignDeadline.Cap::targetDateRaw).orElse(requested);
        int days = target.subtract(start).divide(AdvancePlan.DAY).intValueExact();
        boolean sentinel = ClockStatusRead.available(request.observations().bridgeCapabilities());
        require(actualCap.isEmpty() || sentinel, "campaign advance requires advertised native Arm/Status/Cancel");
        AdvancePlan.ClockMode mode = choice.exactOneDay() && sentinel ? AdvancePlan.ClockMode.EXACT_SENTINEL
                : actualCap.isPresent() ? AdvancePlan.ClockMode.CAMPAIGN_SENTINEL : AdvancePlan.ClockMode.POLLED;
        Optional<WarDailyWatch.Context> watch = actual.flatMap(AdvanceReadiness.Facts::dailyWatch);
        AdvancePlan plan = new AdvancePlan(start, target, days, choice.speed(), choice.policy(), choice.exactOneDay(), mode, actualCap,watch);
        return new ActionCommand(original.actionId(), original.before(), original.source(), original.sessionId(),
                new OperationKey(effectiveStep), original.arguments().with(AdvancePlan.KEY, plan.json()),
                new ExpectedPostcondition(ProposalLifecycle.POSTCONDITION_VERSION, original.before(), original.source(), AdvancePlan.OBSERVER, plan.expected()),
                original.claims(), original.deadline());
    }
}
