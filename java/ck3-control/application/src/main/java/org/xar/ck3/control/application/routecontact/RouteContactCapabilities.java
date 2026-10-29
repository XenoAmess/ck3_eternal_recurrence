package org.xar.ck3.control.application.routecontact;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.routecontact.RouteContactModel.Frame;
import org.xar.ck3.control.application.routecontact.RouteContactModel.TimelineEntry;

/** Admission candidates use the same complete, surviving-history proof producer as execution. */
public final class RouteContactCapabilities {
    private RouteContactCapabilities() { }
    public static List<OperationKey> steps(Frame frame, List<RouteContactProofs.QueryEntry> queries,
            List<? extends TimelineEntry> timeline) {
        java.util.Objects.requireNonNull(frame); java.util.Objects.requireNonNull(queries); java.util.Objects.requireNonNull(timeline);
        if (!frame.mapReady() || !frame.paused() || frame.playerDecision()) return List.of();
        var days = RouteContactProofs.oneDayEntries(frame, queries, timeline);
        List<OperationKey> result = new ArrayList<>();
        boolean windowEligible = frame.ownArmies().stream().filter(RouteContactModel.Army::controllable)
                .noneMatch(army -> army.inCombat() || army.retreating());
        for (var scope : days.keySet()) {
            result.add(new OperationKey(step(scope, 1)));
            for (int count : List.of(2, 3)) if (windowEligible && RouteContactProofs.window(frame, days, scope, count, false).isPresent())
                result.add(new OperationKey(step(scope, count)));
        }
        return result.stream().distinct().sorted(java.util.Comparator.comparing(OperationKey::value)).toList();
    }
    private static String step(RouteContactProofs.Scope scope, int days) {
        String prefix = days == 1 ? "advance-route-contact-horizon-v1-" : "advance-route-contact-window-v1-";
        String suffix = days == 1 ? "" : "-days-" + days;
        return prefix + scope.subjectId() + "-to-" + scope.targetId() + suffix + "-h-" + scope.hostiles().size()
                + "-" + String.join("-", scope.hostiles().stream().map(String::valueOf).toList());
    }
}
