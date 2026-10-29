package org.xar.ck3.control.wave2.finance.projection;

import java.util.List;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.finance.feastcounters.OutcomeCounterConsumerProjectionPort;
import org.xar.ck3.control.wave2.finance.feastcounters.OutcomeCounterNormalizeProjectionPort;
import org.xar.ck3.control.wave2.finance.feastterminal.FeastTerminalProjectionPort;

/** Implemented finance contracts share the one dispatcher and host session. */
public final class FinanceProjectionCatalog implements ProjectionPortCatalog {
    public FinanceProjectionCatalog() { }
    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new WarcashProjectionPort()),
                RegisteredProjection.of(new HolyLoanProjectionPort()),
                RegisteredProjection.of(new RawCashNormalizeProjectionPort()),
                RegisteredProjection.of(new FeastTerminalProjectionPort()),
                RegisteredProjection.of(new OutcomeCounterNormalizeProjectionPort()),
                RegisteredProjection.of(new OutcomeCounterConsumerProjectionPort()));
    }
}
