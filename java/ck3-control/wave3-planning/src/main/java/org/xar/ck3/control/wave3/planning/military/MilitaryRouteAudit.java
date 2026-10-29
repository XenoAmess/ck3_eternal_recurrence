package org.xar.ck3.control.wave3.planning.military;

import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry.*;
import org.xar.ck3.control.military.projectedcontact.SourceBoundContactIndex.Current;
import org.xar.ck3.control.wave3.military.routereroute.RouteReevaluationPlanner.CandidateSource;

/** Ordinary strategy's exact-route geometry and independent one-day native veto.
 * Source: strategy.py:12763-12933,22536-22654. No endpoint projection substitutes for a horizon.
 */
public final class MilitaryRouteAudit {
    private MilitaryRouteAudit() { }
    /** The entire native hostile scope is caller supplied, never inferred from visible geometric conflicts. */
    public record HostileScope(List<Integer> armyIds, List<Enemy> geometricRows, boolean nativeScopeSupported,
                               boolean hostileOperationalOvermatch) {
        public HostileScope {
            armyIds = List.copyOf(armyIds); geometricRows = List.copyOf(geometricRows);
            int prior = -1; for (int value : armyIds) { army(value); StrictJson.require(value > prior, "canonical complete hostile scope required"); prior = value; }
            StrictJson.require(armyIds.size() <= 64, "native hostile scope exceeds 64");
            for (Enemy enemy : geometricRows) { StrictJson.require(enemy.armyId() != null && armyIds.contains(enemy.armyId()), "geometric enemy outside native hostile scope"); }
            StrictJson.require(!nativeScopeSupported || !armyIds.isEmpty(), "supported horizon requires nonempty native hostile scope");
        }
    }
    public record Horizon(Current origin, int armyId, int originProvinceId, int targetProvinceId,
                          List<Integer> hostileArmyIds, List<Integer> subjectRouteProvinceIds, boolean oneDayContactFree) {
        public Horizon {
            Objects.requireNonNull(origin); army(armyId); province(originProvinceId); province(targetProvinceId);
            hostileArmyIds = List.copyOf(hostileArmyIds); hostileArmyIds.forEach(MilitaryRouteAudit::army);
            subjectRouteProvinceIds = provinces(subjectRouteProvinceIds);
        }
        public boolean matches(Current expected, int subject, int originProvince, int target,
                               List<Integer> hostiles, List<Integer> route) {
            return origin.equals(expected) && armyId == subject && originProvinceId == originProvince
                    && targetProvinceId == target && hostileArmyIds.equals(hostiles)
                    && remaining(subjectRouteProvinceIds, originProvince).equals(remaining(route, originProvince));
        }
    }
    public sealed interface HorizonEntry permits ReturnedHorizon, MergeBarrier, RestoreBarrier, FailedHorizon { }
    public record ReturnedHorizon(Horizon value) implements HorizonEntry { public ReturnedHorizon { Objects.requireNonNull(value); } }
    public record MergeBarrier(int destinationArmyId, int sourceArmyId) implements HorizonEntry {
        public MergeBarrier { army(destinationArmyId); army(sourceArmyId); }
    }
    public record RestoreBarrier() implements HorizonEntry { }
    /** A completed exact-frame failure vetoes this candidate. Unknown frame is distinct and also cannot authorize it. */
    public record FailedHorizon(int armyId, int targetProvinceId, List<Integer> hostileArmyIds,
                                Optional<Current> frame, String reason) implements HorizonEntry {
        public FailedHorizon {
            army(armyId); province(targetProvinceId); hostileArmyIds = List.copyOf(hostileArmyIds);
            hostileArmyIds.forEach(MilitaryRouteAudit::army); Objects.requireNonNull(frame); StrictJson.text(reason);
        }
    }
    public sealed interface HorizonLookup permits FoundHorizon, MissingHorizon, UnavailableHorizon { }
    public record FoundHorizon(Horizon value) implements HorizonLookup { public FoundHorizon { Objects.requireNonNull(value); } }
    public record MissingHorizon() implements HorizonLookup { }
    public record UnavailableHorizon(FailedHorizon failure) implements HorizonLookup { public UnavailableHorizon { Objects.requireNonNull(failure); } }

    public static HorizonLookup freshHorizon(List<HorizonEntry> effectiveHistory, Current current, int armyId,
            int originProvinceId, int targetProvinceId, List<Integer> hostiles, List<Integer> route) {
        List<HorizonEntry> history = List.copyOf(effectiveHistory);
        for (int i = history.size() - 1; i >= 0; i--) {
            HorizonEntry entry = history.get(i);
            if (entry instanceof RestoreBarrier || entry instanceof MergeBarrier merge
                    && (merge.destinationArmyId() == armyId || merge.sourceArmyId() == armyId)) return new MissingHorizon();
            if (entry instanceof ReturnedHorizon returned && returned.value().matches(current, armyId, originProvinceId, targetProvinceId, hostiles, route))
                return new FoundHorizon(returned.value());
        }
        // Original fresh lookup considers all valid returned rows before its separate failed-query lookup.
        for (int i = history.size() - 1; i >= 0; i--) {
            HorizonEntry entry = history.get(i);
            if (entry instanceof RestoreBarrier || entry instanceof MergeBarrier merge
                    && (merge.destinationArmyId() == armyId || merge.sourceArmyId() == armyId)) break;
            if (entry instanceof FailedHorizon failure && failure.armyId() == armyId
                    && failure.targetProvinceId() == targetProvinceId && failure.hostileArmyIds().equals(hostiles)) {
                if (failure.frame().isPresent() && !failure.frame().orElseThrow().equals(current)) continue;
                return new UnavailableHorizon(failure);
            }
        }
        return new MissingHorizon();
    }
    public static Audit geometry(List<Integer> completeRoute, int originProvinceId, int targetProvinceId, List<Enemy> enemies) {
        return MilitaryRouteGeometry.geometry(completeRoute, originProvinceId, targetProvinceId, enemies);
    }
    public static Audit consumeHorizon(Audit geometry, Horizon horizon, CandidateSource source, boolean overmatch) {
        Objects.requireNonNull(geometry); Objects.requireNonNull(horizon); Objects.requireNonNull(source);
        if (!horizon.oneDayContactFree()) return new Audit(Status.UNSAFE, geometry.targetProvinceId(), geometry.routeProvinceIds(), geometry.conflicts(), HorizonDecision.NEGATIVE_VETO);
        boolean refuge = source == CandidateSource.PLAYER_HELD_COUNTY_CAPITAL || source == CandidateSource.SAME_REALM_VASSAL_CAPITAL;
        boolean current = geometry.conflicts().stream().anyMatch(value -> value.kind() == ConflictKind.ENEMY_CURRENT_ON_ROUTE);
        if (overmatch && (refuge || current)) return new Audit(geometry.status(), geometry.targetProvinceId(), geometry.routeProvinceIds(), geometry.conflicts(), HorizonDecision.FREE_REJECTED_OPERATIONAL_OVERMATCH);
        return new Audit(Status.SAFE_ONE_DAY_CONTACT_HORIZON, geometry.targetProvinceId(), geometry.routeProvinceIds(), geometry.conflicts(), HorizonDecision.FREE);
    }
    public static String horizonStep(int subject, int target, List<Integer> hostiles) {
        army(subject); province(target); List<Integer> ids = List.copyOf(hostiles); StrictJson.require(!ids.isEmpty() && ids.size() <= 64, "1..64 hostiles required");
        int prior = -1; StringBuilder suffix = new StringBuilder();
        for (int id : ids) { army(id); StrictJson.require(id > prior && id != subject, "canonical disjoint hostiles required"); prior = id; suffix.append('-').append(id); }
        return "query-route-contact-horizon-v1-" + subject + "-to-" + target + "-h-" + ids.size() + suffix;
    }
    public static List<Integer> remaining(List<Integer> route, int origin) { return MilitaryRouteGeometry.remaining(route, origin); }
    private static List<Integer> provinces(List<Integer> values) { List<Integer> result = List.copyOf(values); result.forEach(MilitaryRouteAudit::province); return result; }
    private static void army(int value) { StrictJson.require(value >= 0, "nonnegative public CUnit required"); }
    private static void province(int value) { StrictJson.require(value > 0, "positive Province required"); }
}
