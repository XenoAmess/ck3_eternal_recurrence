package org.xar.ck3.control.application.routecontact;

import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;

/** Canonical existing operation literals; malformed strings never become native requests. */
public final class RouteContactSteps {
    private RouteContactSteps() { }
    public static final String HORIZON = "advance-route-contact-horizon-v1-";
    public static final String WINDOW = "advance-route-contact-window-v1-";
    public static final String QUERY = "query-route-contact-horizon-v1-";
    public record Request(int subjectId, int targetId, List<Integer> hostiles, int days) {
        public Request { RouteContactModel.unit(subjectId); RouteContactModel.province(targetId);
            hostiles = RouteContactModel.canonicalUnits(hostiles, 1, 64); StrictJson.require(!hostiles.contains(subjectId), "subject cannot be hostile");
            StrictJson.require(days >= 1 && days <= 3, "bounded route horizon required"); }
        public RouteContactProofs.Scope scope() { return new RouteContactProofs.Scope(subjectId, targetId, hostiles); }
    }
    public static boolean supports(String value) {
        try { parse(value); return true; }
        catch (IllegalArgumentException unavailable) { return false; }
    }
    public static Request parse(String value) {
        StrictJson.require(value != null && (value.startsWith(HORIZON) || value.startsWith(WINDOW)), "unregistered route contact operation");
        return parse(value, value.startsWith(WINDOW) ? WINDOW : HORIZON);
    }
    public static Request query(String value) { return parse(value, QUERY); }
    private static Request parse(String value, String prefix) {
        StrictJson.require(value != null && value.startsWith(prefix), "exact route operation prefix required"); String[] parts = value.substring(prefix.length()).split("-", -1);
        boolean window = prefix.equals(WINDOW); int marker = window ? 5 : 3; int start = window ? 7 : 5;
        StrictJson.require(parts.length >= start + 1 && parts[1].equals("to") && parts[marker].equals("h")
                && (!window || parts[3].equals("days")), "malformed route operation");
        int subject = number(parts[0]); int target = number(parts[2]); int days = window ? number(parts[4]) : 1; int count = number(parts[marker + 1]);
        List<Integer> hostiles = new ArrayList<>(); for (int index = start; index < parts.length; index++) hostiles.add(number(parts[index]));
        StrictJson.require(count == hostiles.size() && (!window || days == 2 || days == 3), "route scope count/days differ");
        Request result = new Request(subject, target, hostiles, days); StrictJson.require(format(result, prefix).equals(value), "route operation must be canonical"); return result;
    }
    public static String format(Request request, String prefix) {
        return prefix + request.subjectId() + "-to-" + request.targetId() + (prefix.equals(WINDOW) ? "-days-" + request.days() : "")
                + "-h-" + request.hostiles().size() + "-" + String.join("-", request.hostiles().stream().map(Object::toString).toList());
    }
    private static int number(String token) { StrictJson.require(token.matches("0|[1-9][0-9]*"), "canonical decimal operation token required"); return Integer.parseInt(token); }
}
