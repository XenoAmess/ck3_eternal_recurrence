package org.xar.ck3.control.application.planning.governance;

import java.util.Objects;
import org.xar.ck3.control.application.planning.PlanningRequest;
import static org.xar.ck3.control.application.planning.governance.GovernanceObservationSupplier.*;

/** Bind native Council mailbox/public typed producers without registering another operation or synthesizing a read receipt. */
public final class GovernanceCouncilSupplier implements GovernanceObservationSupplier {
    public interface CouncilReadPort {
        Read<CouncilSelection.Query> readPrivate(PlanningRequest request, CouncilSelection.Position position);
        Read<CouncilSelection.Query> readCore(PlanningRequest request);
    }
    private final GovernanceObservationSupplier delegate;
    private final CouncilReadPort council;
    public GovernanceCouncilSupplier(GovernanceObservationSupplier delegate, CouncilReadPort council) {
        this.delegate = Objects.requireNonNull(delegate); this.council = Objects.requireNonNull(council);
    }
    @Override public Read<CouncilSelection.Query> council(PlanningRequest request, CouncilSelection.Position position) {
        return Objects.requireNonNull(council.readPrivate(request, position));
    }
    @Override public Read<CouncilSelection.Query> coreCouncil(PlanningRequest request) { return Objects.requireNonNull(council.readCore(request)); }
    @Override public Read<Durable> durable(PlanningRequest request) { return delegate.durable(request); }
    @Override public Read<Life> lifestyle(PlanningRequest request, String preferredFocus, boolean opening) { return delegate.lifestyle(request, preferredFocus, opening); }
    @Override public Read<OpeningComparison> openingComparison(PlanningRequest request) { return delegate.openingComparison(request); }
    @Override public Read<CouncilRoot> councilRoot(PlanningRequest request) { return delegate.councilRoot(request); }
    @Override public Read<Crown> crown(PlanningRequest request) { return delegate.crown(request); }
    @Override public Read<org.xar.ck3.control.wave3.governance.crownretry.CrownRetryCodec.MatchRequest> crownRetry(PlanningRequest request, String lawKey) {
        return delegate.crownRetry(request, lawKey);
    }
    @Override public Read<org.xar.ck3.control.wave3.governance.crowncooldown.CrownCooldownCodec.ClockRequest> crownCooldown(PlanningRequest request) {
        return delegate.crownCooldown(request);
    }
    @Override public Read<CrownRetryDue.VerifiedDue> crownRetryDue(PlanningRequest request) {
        return delegate.crownRetryDue(request);
    }
}
