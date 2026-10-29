package org.xar.ck3.control.application.advance;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Translation of native_driver's real horizon and speed selectors, using only the starting rich frame. */
public final class AdvancePolicy {
    private AdvancePolicy() { }
    public record Choice(int horizonDays, int speed, String policy, boolean exactOneDay) {
        public Choice { require(horizonDays >= 1 && horizonDays <= 45 && speed >= 1 && speed <= 5, "bounded timeline choice required"); }
    }
    /** Actual same-frame runtime/history admission is consumed here, before the immutable intent is formed. */
    public static Choice select(PlanningRequest request, String step, AdvanceReadiness.Facts actual) {
        require(actual.observed().equals(request.before()), "watch admission differs from the real planning frame");
        Choice base = selectBase(request,step);
        if (actual.dailyWatch().isPresent()) {
            require(step.equals("life-advance-one-day") && base.exactOneDay() && request.observations().actionSteps().contains(new OperationKey("set-speed-2")), "war watch cannot rewrite a different composite or unadvertised speed");
            return new Choice(1,2,WarDailyWatch.POLICY,true);
        }
        if (!base.policy().equals("exact_one_day_noncombat_native_speed_5") && actual.readerUnavailableSpeedFiveReady()) {
            require(step.equals("life-advance-one-day") && base.exactOneDay() && request.observations().actionSteps().contains(new OperationKey("set-speed-5")), "reader rate cannot rewrite a non-exact day or unadvertised speed");
            return new Choice(1,5,ReaderUnavailableSpeed.POLICY,true);
        }
        require(request.observations().actionSteps().contains(new OperationKey("set-speed-" + base.speed())), "selected native timeline speed is not advertised");
        return base;
    }
    public static Choice select(PlanningRequest request, String step) {
        Choice selected = selectBase(request,step);
        require(request.observations().actionSteps().contains(new OperationKey("set-speed-" + selected.speed())), "selected native timeline speed is not advertised");
        return selected;
    }
    private static Choice selectBase(PlanningRequest request, String step) {
        Obj frame = AdvanceHistory.enrichHoldingStates(request.observations().snapshot(), request.observations().history());
        boolean exact = step.equals("life-advance-one-day");
        boolean materialization = new Text(AdvanceHistory.IDENTITY_PENDING).equals(frame.get("battle_control_snapshot_v1_status"));
        if (materialization) {
            require(step.equals("life-advance"), "battle identity materialization requires explicit generic life-advance");
            BigInteger subject = AdvanceHistory.materializationSubject(frame).orElseThrow();
            require(!AdvanceHistory.materializationConsumed(frame, request.observations().history(), subject), "battle identity materialization already consumed for this exact revision");
            exact = true;
        }
        if (exact) require(truth(frame, "paused"), "exact-day advance requires an actual paused map");
        int days = exact ? 1 : horizonDays(frame);
        if (request.observations().bridgeCapabilities().contains("game.command.query-war-results-window-v1")) days = Math.min(days, 8);
        int speed; String policy;
        if (exact) { speed = 1; policy = materialization ? "exact_one_day_battle_identity_materialization" : "exact_one_day_unavoidable_contact"; }
        else if (days != 1) { speed = 5; policy = "bounded_non_tactical"; }
        else if (players(frame).stream().anyMatch(army -> truth(army, "controllable") && (combatOrRetreat(army) || activeRoute(army)))) {
            speed = 1; policy = "player_tactical";
        } else if (assault(frame)) { speed = 1; policy = "player_assault"; }
        else {
            List<Obj> routes = enemyRoutes(frame);
            if (routes.isEmpty() && playerSiege(frame)) { speed = 5; policy = "player_siege"; exact = true; }
            else if (remoteRoutes(frame, routes)) { speed = 3; policy = "remote_enemy_route"; }
            else { speed = 1; policy = "enemy_route_imminent_or_unknown"; }
        }
        if (exact && step.equals("life-advance-one-day") && noncombatFastDay(frame)
                && ClockStatusRead.available(request.observations().bridgeCapabilities())
                && request.observations().actionSteps().contains(new OperationKey("set-speed-5"))) {
            speed = 5; policy = "exact_one_day_noncombat_native_speed_5";
        }
        return new Choice(days, speed, policy, exact);
    }
    public static int horizonDays(Obj frame) {
        for (Obj army : players(frame)) if (truth(army, "controllable") && combatOrRetreat(army)) return 1;
        for (Obj army : players(frame)) if (truth(army, "controllable") && activeRoute(army)) return 1;
        if (!enemyRoutes(frame).isEmpty()) return 1;
        if (truth(frame, "paused") && (assault(frame) || playerSiege(frame) && truth(frame, "war_objective_siege_progress_supported"))) return 1;
        return wars(frame).isEmpty() ? 30 : 7;
    }
    public static boolean noncombatFastDay(Obj frame) {
        if (!truth(frame, "paused") || !truth(frame, "map_ready") || present(frame.get("active_event"))
                || present(frame.get("pending_character_interaction")) || !truth(frame, "war_objective_assault_supported")
                || modalPresent(frame) || assault(frame)) return false;
        for (Obj army : players(frame)) if (!truth(army, "controllable") || !falsehood(army, "in_combat")
                || !falsehood(army, "retreating") || combatOrRetreat(army)) return false;
        return true;
    }
    public static boolean assault(Obj frame) {
        if (!truth(frame, "war_objective_assault_supported")) return false;
        return siegeStates(frame).stream().anyMatch(state -> truth(state, "siege_observable")
                && state.get("active_siege") instanceof Obj siege && truth(siege, "player_army_besieging")
                && truth(siege, "assault_observable") && truth(siege, "assault_in_progress"));
    }
    public static boolean playerSiege(Obj frame) {
        if (!truth(frame, "paused")) return false;
        for (Obj state : siegeStates(frame)) {
            if (!truth(state, "siege_observable") || !(state.get("active_siege") instanceof Obj siege)) continue;
            if (truth(siege, "player_army_besieging")) return true;
            // Published native occurrence qualification supplies the same contribution predicate.
            if (state.get("province_unit_occurrences") instanceof Arr occurrences) {
                for (Obj army : players(frame)) {
                    if (!truth(army, "controllable") || !java.util.Objects.equals(state.get("province_id"), army.get("current_province_id"))
                            || army.get("move_target_province_id") != Nil.INSTANCE
                            || !(army.get("route_province_ids") instanceof Arr route) || !route.items().isEmpty()) continue;
                    List<Obj> matches = objects(occurrences, "province_unit_occurrences").stream()
                            .filter(row -> java.util.Objects.equals(row.get("public_unit_id"), army.get("army_id"))).toList();
                    if (!matches.isEmpty() && matches.stream().allMatch(row -> truth(row, "eligible"))) return true;
                }
            }
        }
        return false;
    }
    private static boolean remoteRoutes(Obj frame, List<Obj> routes) {
        if (!truth(frame, "army_routes_supported") || !truth(frame, "war_objective_assault_supported") || routes.isEmpty()
                || routes.stream().anyMatch(army -> !auditableRoute(army))) return false;
        List<Obj> players = players(frame); List<Obj> wars = wars(frame);
        if (players.isEmpty() || wars.isEmpty()) return false;
        Map<BigInteger, Obj> byId = new HashMap<>(); Set<BigInteger> provinces = new HashSet<>();
        for (Obj army : players) {
            if (!truth(army, "controllable") || !positive(army.get("army_id")) || !positive(army.get("current_province_id"))
                    || !routeComplete(army) || !(state(army).equals("regular") || state(army).equals("sieging")
                    || state(army).isEmpty() && (code(army, 1) || code(army, 3))) || combatOrRetreat(army) || activeRoute(army)) return false;
            if (byId.put(integer(army.get("army_id"), "army_id"), army) != null) return false;
            provinces.add(integer(army.get("current_province_id"), "current_province_id"));
        }
        Set<BigInteger> observed = new HashSet<>(); Map<BigInteger, List<Value>> enemiesSeen = new HashMap<>();
        for (Obj war : wars) {
            if (!(war.get("allied_armies") instanceof Arr allies) || !(war.get("enemy_armies") instanceof Arr enemies)) return false;
            Set<BigInteger> allied = new HashSet<>();
            for (Obj ally : objects(allies, "allied_armies")) {
                if (!truth(ally, "controllable")) continue;
                if (!positive(ally.get("army_id")) || !positive(ally.get("current_province_id"))) return false;
                BigInteger id = integer(ally.get("army_id"), "army_id");
                if (!allied.add(id) || !byId.containsKey(id) || !tactical(ally).equals(tactical(byId.get(id)))) return false;
            }
            if (!allied.equals(byId.keySet())) return false;
            Set<BigInteger> inWar = new HashSet<>();
            for (Obj enemy : objects(enemies, "enemy_armies")) {
                if (retreating(enemy)) continue;
                if (!positive(enemy.get("army_id")) || !positive(enemy.get("current_province_id")) || !routeComplete(enemy)) return false;
                BigInteger id = integer(enemy.get("army_id"), "army_id");
                if (!inWar.add(id) || provinces.contains(integer(enemy.get("current_province_id"), "current_province_id"))) return false;
                List<Value> projection = tactical(enemy); List<Value> previous = enemiesSeen.putIfAbsent(id, projection);
                if (previous != null && !previous.equals(projection)) return false;
                if (!activeRoute(enemy)) continue;
                if (!auditableRoute(enemy) || array(enemy.get("route_province_ids"), "route").stream().anyMatch(value -> provinces.contains(integer(value, "route province")))) return false;
                observed.add(id);
            }
        }
        return observed.equals(routes.stream().map(army -> integer(army.get("army_id"), "army_id")).collect(java.util.stream.Collectors.toSet()));
    }
    private static boolean routeComplete(Obj army) {
        String state = state(army); Value target = army.get("move_target_province_id");
        return (target == Nil.INSTANCE || positive(target)) && army.get("route_province_ids") instanceof Arr route
                && route.items().stream().allMatch(AdvancePolicy::positive)
                && (Set.of("regular", "combat", "sieging", "gathering", "moving").contains(state)
                    || state.isEmpty() && (code(army, 1) || code(army, 2) || code(army, 3) || code(army, 5) || code(army, 7)));
    }
    private static boolean auditableRoute(Obj army) {
        return positive(army.get("move_target_province_id")) && army.get("route_province_ids") instanceof Arr route
                && !route.items().isEmpty() && route.items().stream().allMatch(AdvancePolicy::positive)
                && route.items().getLast().equals(army.get("move_target_province_id"));
    }
    private static List<Value> tactical(Obj army) {
        List<Value> values = new ArrayList<>();
        for (String key : List.of("army_id", "current_province_id", "move_target_province_id", "route_province_ids", "army_state_code", "in_combat", "retreating", "controllable"))
            values.add(army.get(key) == null ? Nil.INSTANCE : army.get(key));
        values.add(new Text(state(army))); return List.copyOf(values);
    }
    public static boolean combatOrRetreat(Obj army) { return truth(army, "in_combat") || retreating(army) || state(army).equals("combat") || code(army, 2); }
    public static boolean retreating(Obj army) { return truth(army, "retreating") || state(army).equals("retreating") || code(army, 6); }
    public static boolean activeRoute(Obj army) { return positive(army.get("move_target_province_id")) || army.get("route_province_ids") instanceof Arr route && !route.items().isEmpty() || state(army).equals("moving") || code(army, 7); }
    public static boolean modalPresent(Obj frame) { return frame.get("top_exclusive_modal_choice_hint") instanceof Obj hint && new Text("present").equals(hint.get("status")); }
    public static boolean truth(Obj row, String key) { return new Bool(true).equals(row.get(key)); }
    public static boolean falsehood(Obj row, String key) { return new Bool(false).equals(row.get(key)); }
    public static boolean present(Value value) { return value != null && value != Nil.INSTANCE; }
    public static boolean positive(Value value) { return value instanceof IntegerValue number && number.value().signum() > 0; }
    private static String state(Obj army) { return army.get("army_state") instanceof Text value ? value.value().toLowerCase(Locale.ROOT) : ""; }
    private static boolean code(Obj army, int code) { return new IntegerValue(BigInteger.valueOf(code)).equals(army.get("army_state_code")); }
    public static List<Obj> players(Obj frame) { return objects(frame.get("player_armies"), "player_armies"); }
    public static List<Obj> wars(Obj frame) { return objects(frame.get("active_wars"), "active_wars"); }
    public static List<Obj> objects(Value value, String name) {
        if (value == null || value == Nil.INSTANCE) return List.of();
        return array(value, name).stream().map(item -> object(item, name + " row")).toList();
    }
    private static List<Obj> enemyRoutes(Obj frame) {
        return wars(frame).stream().flatMap(war -> objects(war.get("enemy_armies"), "enemy_armies").stream())
                .filter(army -> !retreating(army) && activeRoute(army)).toList();
    }
    public static List<Obj> siegeStates(Obj frame) {
        List<Obj> rows = new ArrayList<>();
        wars(frame).forEach(war -> rows.addAll(objects(war.get("objective_province_states"), "objective_province_states")));
        rows.addAll(objects(frame.get("_queried_holding_siege_states"), "_queried_holding_siege_states"));
        return List.copyOf(rows);
    }
}
