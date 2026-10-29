package org.xar.ck3.control.wave3.planning.military;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;

/** Shared pure ordinary route geometry, strategy.py:22536-22654. No native/AI source provider or action port. */
public final class MilitaryRouteGeometry {
    private MilitaryRouteGeometry() { }

    public enum TacticalState { RETREATING, OTHER }
    public record Enemy(Integer armyId, Optional<Integer> currentProvinceId, Optional<Integer> targetProvinceId,
                        List<Integer> routeProvinceIds, TacticalState state) {
        public Enemy {
            if (armyId != null) army(armyId); Objects.requireNonNull(currentProvinceId); Objects.requireNonNull(targetProvinceId);
            currentProvinceId.ifPresent(MilitaryRouteGeometry::province); targetProvinceId.ifPresent(MilitaryRouteGeometry::province);
            routeProvinceIds = provinces(routeProvinceIds); Objects.requireNonNull(state);
        }
    }
    public enum ConflictKind { ENEMY_CURRENT_ON_ROUTE, ENEMY_TARGET_ON_ROUTE, SHARED_NEXT_HOP,
        ENEMY_ROUTE_INTERSECTION, OPPOSITE_EDGE_INTERSECTION }
    public record Conflict(ConflictKind kind, Integer enemyArmyId, int provinceId,
                           Optional<Integer> toProvinceId, Optional<Integer> playerHop, Optional<Integer> enemyHop) {
        public Conflict {
            Objects.requireNonNull(kind); if (enemyArmyId != null) army(enemyArmyId); province(provinceId); Objects.requireNonNull(toProvinceId);
            toProvinceId.ifPresent(MilitaryRouteGeometry::province); Objects.requireNonNull(playerHop); Objects.requireNonNull(enemyHop);
        }
    }
    public enum Status { SAFE, UNSAFE, ROUTE_DOES_NOT_REACH_TARGET, SAFE_ONE_DAY_CONTACT_HORIZON }
    public enum HorizonDecision { NOT_REQUESTED, NEGATIVE_VETO, FREE, FREE_REJECTED_OPERATIONAL_OVERMATCH }
    public record Audit(Status status, int targetProvinceId, List<Integer> routeProvinceIds,
                        List<Conflict> conflicts, HorizonDecision horizonDecision) {
        public Audit {
            Objects.requireNonNull(status); province(targetProvinceId); routeProvinceIds = provinces(routeProvinceIds);
            conflicts = List.copyOf(conflicts); Objects.requireNonNull(horizonDecision);
        }
        public boolean accepted() { return status == Status.SAFE || status == Status.SAFE_ONE_DAY_CONTACT_HORIZON; }
        public boolean battleWinProbabilityKnown() { return false; }
        public boolean movementAuthorized() { return false; }
    }
    public static Audit geometry(List<Integer> completeRoute, int originProvinceId, int targetProvinceId, List<Enemy> enemies) {
        StrictJson.require(originProvinceId >= 0, "nonnegative origin/sentinel required"); province(targetProvinceId);
        List<Integer> route = remaining(provinces(completeRoute), originProvinceId);
        if (route.isEmpty() || route.getLast() != targetProvinceId)
            return new Audit(Status.ROUTE_DOES_NOT_REACH_TARGET, targetProvinceId, route, List.of(), HorizonDecision.NOT_REQUESTED);
        var routeSet = new HashSet<>(route); List<Conflict> conflicts = new ArrayList<>();
        for (Enemy enemy : List.copyOf(enemies)) {
            if (enemy.state() == TacticalState.RETREATING) continue;
            enemy.currentProvinceId().filter(routeSet::contains).ifPresent(value -> conflicts.add(conflict(ConflictKind.ENEMY_CURRENT_ON_ROUTE, enemy.armyId(), value)));
            enemy.targetProvinceId().filter(routeSet::contains).ifPresent(value -> conflicts.add(conflict(ConflictKind.ENEMY_TARGET_ON_ROUTE, enemy.armyId(), value)));
            List<Integer> other = enemy.currentProvinceId().isPresent()
                    ? remaining(enemy.routeProvinceIds(), enemy.currentProvinceId().orElseThrow()) : enemy.routeProvinceIds();
            if (!other.isEmpty() && other.getFirst().equals(route.getFirst())) conflicts.add(conflict(ConflictKind.SHARED_NEXT_HOP, enemy.armyId(), route.getFirst()));
            Map<Integer, Integer> hops = new HashMap<>();
            for (int i = 0; i < other.size(); i++) hops.putIfAbsent(other.get(i), i + 1);
            for (int i = 0; i < route.size(); i++) {
                Integer hop = hops.get(route.get(i)); if (hop != null) conflicts.add(new Conflict(ConflictKind.ENEMY_ROUTE_INTERSECTION,
                        enemy.armyId(), route.get(i), Optional.empty(), Optional.of(i + 1), Optional.of(hop)));
            }
            Map<Edge, Integer> reverse = new HashMap<>();
            for (int i = 0; i + 1 < other.size(); i++) reverse.put(new Edge(other.get(i + 1), other.get(i)), i + 1);
            for (int i = 0; i + 1 < route.size(); i++) {
                Integer hop = reverse.get(new Edge(route.get(i), route.get(i + 1)));
                if (hop != null) conflicts.add(new Conflict(ConflictKind.OPPOSITE_EDGE_INTERSECTION, enemy.armyId(), route.get(i),
                        Optional.of(route.get(i + 1)), Optional.of(i + 1), Optional.of(hop)));
            }
        }
        return new Audit(conflicts.isEmpty() ? Status.SAFE : Status.UNSAFE, targetProvinceId, route, conflicts, HorizonDecision.NOT_REQUESTED);
    }
    public static List<Integer> remaining(List<Integer> route, int origin) { return !route.isEmpty() && route.getFirst() == origin ? List.copyOf(route.subList(1, route.size())) : List.copyOf(route); }
    private record Edge(int origin, int target) { }
    private static Conflict conflict(ConflictKind kind, Integer enemy, int province) { return new Conflict(kind, enemy, province, Optional.empty(), Optional.empty(), Optional.empty()); }
    private static List<Integer> provinces(List<Integer> values) { List<Integer> result = List.copyOf(values); result.forEach(MilitaryRouteGeometry::province); return result; }
    private static void army(int value) { StrictJson.require(value >= 0, "nonnegative public CUnit required"); }
    private static void province(int value) { StrictJson.require(value > 0, "positive Province required"); }
}
