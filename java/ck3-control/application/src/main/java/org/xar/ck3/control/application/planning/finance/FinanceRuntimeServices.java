package org.xar.ck3.control.application.planning.finance;

import java.util.Objects;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;

/** The one actual finance read/policy graph for one physical Game and session. */
public record FinanceRuntimeServices(GameGeneration game,String sessionId,G2Source source,FinanceReadContracts definitions,
        FinanceStatePort state,OrdinaryFinanceCollector collector,OrdinaryFinancePolicies policies,PlanningReadPort readPort,CanonicalFundingPending fundingPending,org.xar.ck3.control.application.planning.finance.publicgift.FactionGiftPublicPort publicGifts) {
    public FinanceRuntimeServices {
        Objects.requireNonNull(game);StrictJson.text(sessionId);Objects.requireNonNull(source);Objects.requireNonNull(definitions);
        Objects.requireNonNull(state);Objects.requireNonNull(collector);Objects.requireNonNull(policies);Objects.requireNonNull(readPort);Objects.requireNonNull(fundingPending);Objects.requireNonNull(publicGifts);
    }
}
