package org.xar.ck3.control.application.planning.governance;

import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.application.planning.OrdinaryCorePolicy;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.contracts.ExactRef;

/** Concrete ordinary factories; every returned stage has its real domain producer. */
public final class OrdinaryGovernancePolicies {
    private final GovernancePolicies.Opening opening;
    private final GovernancePolicies.Lifestyle lifestyle;
    private final GovernancePolicies.Council council;
    private final GovernancePolicies.Crown crown;
    private final OrdinaryFeastPolicy feast;

    public OrdinaryGovernancePolicies(GovernanceObservationSupplier delegate, GovernanceCouncilSupplier.CouncilReadPort councilReads,
            ExactRef governanceSource, OrdinaryFeastPolicy feast) {
        Objects.requireNonNull(delegate); Objects.requireNonNull(governanceSource);
        var governance = new GovernanceCouncilSupplier(delegate, councilReads);
        this.feast = Objects.requireNonNull(feast);
        opening = new GovernancePolicies.Opening(governance, governanceSource);
        lifestyle = new GovernancePolicies.Lifestyle(governance, governanceSource);
        council = new GovernancePolicies.Council(governance, governanceSource);
        crown = new GovernancePolicies.Crown(governance, governanceSource);
    }

    /** The sole planner orders these by PlanningStage, rejecting duplicate owners. */
    public List<OrdinaryPolicy> stages() { return List.of(opening, lifestyle, council, crown, feast); }

    /** Bind at the original peaceful-core Council19 call site, before marriage and war entry. */
    public OrdinaryCorePolicy.CoreProducer coreCouncil() { return council::evaluateCoreCouncil; }
}
