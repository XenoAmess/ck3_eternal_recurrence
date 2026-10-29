package org.xar.ck3.control.wave3.military.routereroute;

import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.military.routereroute.RouteReroutePolicy.*;

/** Source-bound route consumers. They produce planning data and existing preview requests, without a submitter. */
public final class RoutePlanningConsumer {
    private RoutePlanningConsumer() { }
    /** Concrete ordinary ranked-preview consumer. Available routes continue into the independent native contact audit. */
    public static RouteReevaluationPlanner.Result planOrdinary(byte[] exactLookupPacket,
            RouteReevaluationPlanner.Context context, List<RouteReevaluationPlanner.Objective> orderedObjectives,
            List<String> availableSteps) {
        return RouteReevaluationPlanner.plan(RoutePreviewConsumerCodec.decode(exactLookupPacket), context,
                orderedObjectives, availableSteps);
    }
    public static CacheScope bindInputs(CacheScope observedScope, byte[] exactLookupPacket, List<Goal> orderedGoals) {
        return new CacheScope(observedScope.machineId(), observedScope.executableSha256(), observedScope.lease(),
                observedScope.dateRaw(), observedScope.armyId(), observedScope.currentProvinceId(), observedScope.committedRoute(),
                observedScope.movement(), observedScope.hostileScopeSha256(), observedScope.nativeLegalitySha256(),
                goalDigest(orderedGoals), StockRouteRuleReader.sha256(exactLookupPacket));
    }
    public static Plan plan(byte[] exactLookupPacket, CacheScope observedScope, List<Goal> orderedGoals, Cache prior) {
        Lookup input = RoutePreviewConsumerCodec.decode(exactLookupPacket);
        StrictJson.require(observedScope.historySha256().equals(StockRouteRuleReader.sha256(exactLookupPacket)),
                "actual readonly history differs from cache source binding");
        StrictJson.require(observedScope.goalOrderingSha256().equals(goalDigest(orderedGoals)),
                "actual ranked goals differ from cache source binding");
        Query query = input.query();
        StrictJson.require(query.armyId() == observedScope.armyId() && query.originProvinceId() == observedScope.currentProvinceId()
                && query.dateRaw().isPresent() && query.dateRaw().orElseThrow() == observedScope.dateRaw()
                && query.expectedLease().isPresent() && query.expectedLease().orElseThrow().equals(observedScope.lease()),
                "actual preview consumer frame/army scope differs");
        return RouteReroutePolicy.selectRanked(input.history(), observedScope, orderedGoals, prior);
    }
    private static String goalDigest(List<Goal> orderedGoals) {
        var array = StrictJson.object().putArray("goals");
        for (Goal goal : orderedGoals) {
            var row = array.addObject(); row.put("target_province_id", goal.targetProvinceId());
            row.put("blocked", goal.blocked()); row.put("qualified_contact", goal.qualifiedContact());
        }
        return StockRouteRuleReader.sha256(StrictJson.canonical(array, 1_048_576));
    }
}
