package org.xar.ck3.control.nativebridge.capabilities.frontend_rules;

import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;

/** Exact source-bound route and revision profile of a physically installed callable. */
public record FrontendRouteAdmission(OperationKey operation, Set<FrontendRulesData.Route> routes,
        FrameMode frameMode, ExactRef source) {
    public enum FrameMode { MENU, SNAPSHOT }
    public FrontendRouteAdmission {
        Objects.requireNonNull(operation); routes = Set.copyOf(routes); Objects.requireNonNull(frameMode); Objects.requireNonNull(source);
        StrictJson.require(!routes.isEmpty() && !routes.contains(FrontendRulesData.Route.UNAVAILABLE) && source.bytes() > 0,
                "actual nonempty frontend routes and installer source required");
    }
}
