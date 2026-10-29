package org.xar.ck3.control.wave2.military.routewindowstep;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.TreeSet;
import org.xar.ck3.control.contracts.StrictJson;

/** Canonical request identity only; constructing a step does not admit clock advancement. */
public record RouteWindowStep(int subjectArmyId, int targetProvinceId, List<Integer> hostileArmyIds, int horizonDays) {
    public static final String PREFIX = "advance-route-contact-window-v1-";

    public RouteWindowStep {
        StrictJson.require(subjectArmyId >= 0 && targetProvinceId > 0, "public CUnit and positive Province int32 required");
        StrictJson.require(horizonDays == 2 || horizonDays == 3, "route step requires two or three days");
        StrictJson.require(hostileArmyIds != null, "complete hostile sequence required");
        TreeSet<Integer> canonical = new TreeSet<>();
        for (Integer hostile : hostileArmyIds) {
            StrictJson.require(hostile != null && hostile >= 0, "public hostile CUnit int32 required"); canonical.add(hostile);
        }
        StrictJson.require(!canonical.isEmpty() && canonical.size() <= 64 && !canonical.contains(subjectArmyId),
                "route window hostile scope malformed");
        hostileArmyIds = List.copyOf(canonical);
    }

    public String canonical() {
        StringBuilder result = new StringBuilder(PREFIX).append(subjectArmyId).append("-to-")
                .append(targetProvinceId).append("-days-").append(horizonDays).append("-h-").append(hostileArmyIds.size());
        for (Integer hostile : hostileArmyIds) { result.append('-').append(hostile); }
        return result.toString();
    }

    public static Optional<RouteWindowStep> parse(String value) {
        if (value == null || !value.startsWith(PREFIX)) { return Optional.empty(); }
        String[] parts = value.substring(PREFIX.length()).split("-", -1);
        if (parts.length < 8 || !parts[1].equals("to") || !parts[3].equals("days") || !parts[5].equals("h")) {
            return Optional.empty();
        }
        try {
            int subject = decimal(parts[0]); int target = decimal(parts[2]); int days = decimal(parts[4]);
            int count = decimal(parts[6]); if (count != parts.length - 7) { return Optional.empty(); }
            List<Integer> hostiles = new ArrayList<>();
            for (int index = 7; index < parts.length; index++) { hostiles.add(decimal(parts[index])); }
            RouteWindowStep result = new RouteWindowStep(subject, target, hostiles, days);
            return result.canonical().equals(value) ? Optional.of(result) : Optional.empty();
        } catch (IllegalArgumentException error) { return Optional.empty(); }
    }

    private static int decimal(String value) {
        StrictJson.require(!value.isEmpty() && (value.equals("0") || value.charAt(0) != '0'), "canonical decimal required");
        for (int index = 0; index < value.length(); index++) {
            char digit = value.charAt(index); StrictJson.require(digit >= '0' && digit <= '9', "ASCII decimal required");
        }
        return Integer.parseInt(value);
    }
}
