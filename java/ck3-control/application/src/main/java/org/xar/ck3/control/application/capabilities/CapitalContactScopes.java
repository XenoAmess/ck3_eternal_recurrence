package org.xar.ck3.control.application.capabilities;

import static org.xar.ck3.control.application.capabilities.CapabilityJson.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.Set;

/** Exact source-bound R838/R0103 regroup and R0088 read-only hold selectors. */
public final class CapitalContactScopes {
    public record Scope(int armyId,int capitalProvinceId,List<Integer> hostileArmyIds) {
        public Scope { hostileArmyIds = List.copyOf(hostileArmyIds); }
    }
    private CapitalContactScopes() { }

    public static Optional<Scope> capitalRegroupScope(Obj snapshot,Obj cachedQuery) {
        Obj root = boundRoot(snapshot,cachedQuery).orElse(null);
        if (root == null || !int32Id(root.get("capital_province_id"))) return Optional.empty();
        int capital = idAt(root,"capital_province_id");
        Obj readiness = obj(root.get("readiness")).orElse(null), player = obj(snapshot.get("played_character")).orElse(null);
        List<Obj> wars = rows(snapshot.get("active_wars")), controlled = rows(snapshot.get("player_armies")).stream().filter(a -> yes(a,"controllable")).toList();
        if (wars.size() != 1 || !(snapshot.get("player_armies") instanceof Arr)) return Optional.empty();
        Obj war = wars.getFirst(); Value actor = player == null ? null : player.get("character_id");
        boolean attacker = named(war,"player_side","attacker"), defender = named(war,"player_side","defender");
        boolean nonleader = attacker && no(war,"player_is_primary_war_leader") && controlled.size() == 1 && yes(player,"alive")
                && eq(controlled.getFirst(),"owner_character_id",actor) && yes(controlled.getFirst(),"controllable")
                && yes(snapshot,"route_contact_horizon_supported") && yes(readiness,"held_title_partition_ready")
                && scoreInside(war,-100,100);
        if (controlled.isEmpty() || !(yes(war,"player_is_primary_war_leader") || nonleader)) return Optional.empty();
        if (attacker) for (String field : List.of("war_objective_occupation_supported","war_objective_garrison_supported","war_objective_siege_progress_supported","war_objective_assault_supported"))
            if (!yes(snapshot,field)) return Optional.empty();
        if (nonleader && !countyCapitals(root,true).filter(values -> values.contains(capital)).isPresent()) return Optional.empty();
        if (defender) {
            if (!yes(snapshot,"route_contact_horizon_supported") || !yes(readiness,"held_title_partition_ready")
                    || !(root.get("held_title_partition") instanceof Arr) || controlled.size() != 1
                    || !(war.get("war_objective_province_ids") instanceof Arr objectives) || objectives.items().isEmpty()
                    || objectives.items().stream().anyMatch(v -> !positive(v)) || !scoreInside(war,-100,0)
                    || !countyCapitals(root,false).filter(values -> values.contains(capital)).isPresent()) return Optional.empty();
            Obj army = controlled.getFirst();
            if (!positive(army.get("move_target_province_id")) || !objectives.items().contains(army.get("move_target_province_id"))
                    || eq(army,"move_target_province_id",root.get("capital_province_id"))
                    || !(army.get("route_province_ids") instanceof Arr route) || route.items().isEmpty()
                    || route.items().stream().anyMatch(v -> !positive(v)) || !route.items().getLast().equals(army.get("move_target_province_id"))
                    || NativeActionSteps.combatOrRetreat(army)) return Optional.empty();
        }
        if (!attacker && !defender) return Optional.empty();
        String sole = controlled.size() == 1 ? lower(controlled.getFirst(),"army_state") : null;
        boolean coalition = defender || controlled.size() > 1 || "regular".equals(sole) || "moving".equals(sole);
        Obj army;
        if (coalition) {
            List<Obj> away = controlled.stream().filter(a -> int32Id(a.get("current_province_id"))
                    && !eq(a,"current_province_id",root.get("capital_province_id")) && !NativeActionSteps.combatOrRetreat(a)).toList();
            if (away.size() != 1) return Optional.empty();
            army = away.getFirst();
            for (Obj candidate : controlled) if (NativeActionSteps.combatOrRetreat(candidate)
                    || candidate != army && !(eq(candidate,"current_province_id",root.get("capital_province_id"))
                    && NativeActionSteps.stationary(candidate) && nil(candidate,"move_target_province_id") && emptyArray(candidate,"route_province_ids"))) return Optional.empty();
        } else army = controlled.getFirst();
        String state = lower(army,"army_state");
        boolean admittedState = state != null ? coalition ? Set.of("regular","moving","sieging").contains(state) : "sieging".equals(state)
                : number(army.get("army_state_code")).filter(v -> coalition ? Set.of(BigInteger.ONE,BigInteger.valueOf(3),BigInteger.valueOf(7)).contains(v) : v.equals(BigInteger.valueOf(3))).isPresent();
        if (!unitId(army.get("army_id")) || !int32Id(army.get("current_province_id"))
                || eq(army,"current_province_id",root.get("capital_province_id")) || !admittedState || NativeActionSteps.combatOrRetreat(army)
                || !army.members().containsKey("move_target_province_id") || !(nil(army,"move_target_province_id") || coalition && positive(army.get("move_target_province_id")))
                || !(army.get("route_province_ids") instanceof Arr route) || !coalition && !route.items().isEmpty()) return Optional.empty();
        if (defender && !(state != null ? "moving".equals(state) : eq(army,"army_state_code",new IntegerValue(BigInteger.valueOf(7))))) return Optional.empty();
        if (!coalition) {
            if (!(war.get("war_objective_province_ids") instanceof Arr objectives) || !objectives.items().equals(List.of(army.get("current_province_id")))
                    || !(war.get("objective_province_states") instanceof Arr states) || states.items().size() != 1 || !(states.items().getFirst() instanceof Obj objective)) return Optional.empty();
            Obj siege = obj(objective.get("active_siege")).orElse(null);
            if (!eq(objective,"province_id",army.get("current_province_id")) || !yes(objective,"occupation_observable") || !no(objective,"is_occupied")
                    || !yes(objective,"siege_observable") || siege == null || !positive(siege.get("siege_id")) || !eq(siege,"besieging_army_id",army.get("army_id"))
                    || !yes(siege,"player_army_besieging") || !yes(siege,"assault_observable") || !no(siege,"assault_in_progress")
                    || !eq(objective,"besieging_strength",new IntegerValue(BigInteger.valueOf(399))) || !eq(objective,"garrison_size",new IntegerValue(BigInteger.valueOf(400)))) return Optional.empty();
        }
        List<Obj> enemies = NativeActionSteps.enemies(List.of(war)).stream().filter(e -> !NativeActionSteps.retreating(e)).toList();
        Optional<List<Integer>> hostiles = completeEnemies(enemies,false,capital);
        if (hostiles.isEmpty()) return Optional.empty();
        if (defender) {
            Set<Value> routeIds = new HashSet<>(route.items()); boolean intersects = false;
            for (Obj enemy : enemies) if (routeIds.contains(enemy.get("current_province_id"))
                    || arrayOrEmpty(enemy.get("route_province_ids")).orElseThrow().stream().anyMatch(routeIds::contains)) intersects = true;
            if (!intersects) return Optional.empty();
        }
        return Optional.of(new Scope(integerAt(army,"army_id").intValueExact(),capital,hostiles.orElseThrow()));
    }

    public static Optional<Scope> alliedCapitalHoldScope(Obj snapshot,Obj cachedQuery) {
        Obj root = boundRoot(snapshot,cachedQuery).orElse(null);
        if (root == null || !yes(snapshot,"route_contact_horizon_supported") || !int32Id(root.get("capital_province_id"))) return Optional.empty();
        Obj readiness = obj(root.get("readiness")).orElse(null); int capital = idAt(root,"capital_province_id");
        if (!yes(readiness,"held_title_partition_ready") || !countyCapitals(root,true).filter(values -> values.contains(capital)).isPresent()) return Optional.empty();
        List<Obj> wars = rows(snapshot.get("active_wars")), controlled = rows(snapshot.get("player_armies")).stream().filter(a -> yes(a,"controllable")).toList();
        if (wars.size() != 1 || controlled.size() != 1) return Optional.empty();
        Obj war = wars.getFirst(), army = controlled.getFirst();
        if (!named(war,"player_side","attacker") || !no(war,"player_is_primary_war_leader") || !emptyArray(war,"war_objective_province_ids") || !emptyArray(war,"objective_province_states")
                || !unitId(army.get("army_id")) || !eq(army,"current_province_id",root.get("capital_province_id")) || !named(army,"army_state","regular")
                || !NativeActionSteps.stationary(army) || NativeActionSteps.combatOrRetreat(army) || !army.members().containsKey("move_target_province_id")
                || !nil(army,"move_target_province_id") || !emptyArray(army,"route_province_ids")) return Optional.empty();
        return completeEnemies(NativeActionSteps.enemies(List.of(war)),true,capital)
                .map(ids -> new Scope(integerAt(army,"army_id").intValueExact(),capital,ids));
    }
    private static Optional<Obj> boundRoot(Obj snapshot,Obj query) {
        if (snapshot == null || query == null || !yes(snapshot,"paused") || !yes(snapshot,"map_ready")
                || !nil(snapshot,"active_event") || !nil(snapshot,"pending_character_interaction")) return Optional.empty();
        Obj diagnostics = obj(snapshot.get("diagnostics")).orElse(null), binding = obj(query.get("cache_binding")).orElse(null), root = obj(query.get("campaign_root_context")).orElse(null);
        Obj player = obj(snapshot.get("played_character")).orElse(null);
        if (diagnostics == null || binding == null || root == null || player == null || !int32Id(player.get("character_id"))) return Optional.empty();
        for (String key : List.of("snapshot_id","revision","native_revision","date_raw")) if (!equalField(binding,key,snapshot,key)) return Optional.empty();
        if (!eq(binding,"actor_character_id",player.get("character_id")) || !equalField(binding,"bridge_pid",diagnostics,"bridge_pid")
                || !equalField(binding,"connection_generation",diagnostics,"connection_generation") || !named(root,"status","available")
                || !equalField(root,"snapshot_revision",snapshot,"native_revision") || !equalField(root,"date_raw",snapshot,"date_raw") || !eq(root,"player_character_id",player.get("character_id"))
                || !yes(obj(root.get("readiness")).orElse(null),"ready")) return Optional.empty();
        return Optional.of(root);
    }
    private static Optional<List<Integer>> countyCapitals(Obj root,boolean strictTitles) {
        if (!(root.get("held_title_partition") instanceof Arr partition)) return Optional.empty();
        List<Integer> capitals = new ArrayList<>();
        for (Value value : partition.items()) {
            if (!(value instanceof Obj row) || !(row.get("title") instanceof Obj title)) return Optional.empty();
            if (strictTitles && (!positive(title.get("title_id")) || !(title.get("tier_raw") instanceof IntegerValue))) return Optional.empty();
            if (!eq(title,"tier_raw",new IntegerValue(BigInteger.TWO))) continue;
            if (!int32Id(row.get("capital_province_id"))) return Optional.empty();
            capitals.add(idAt(row,"capital_province_id"));
        }
        if (strictTitles && new HashSet<>(capitals).size() != capitals.size()) return Optional.empty();
        return Optional.of(List.copyOf(capitals));
    }
    private static Optional<List<Integer>> completeEnemies(List<Obj> enemies,boolean alliedHold,int capital) {
        if (enemies.isEmpty() || enemies.size() > 64) return Optional.empty();
        List<Integer> ids = new ArrayList<>();
        for (Obj enemy : enemies) {
            if (!int32Id(enemy.get("army_id")) || !int32Id(enemy.get("current_province_id")) || !enemy.members().containsKey("move_target_province_id")
                    || !(enemy.get("route_province_ids") instanceof Arr route) || route.items().stream().anyMatch(v -> !positive(v))) return Optional.empty();
            if (alliedHold) {
                if (eq(enemy,"current_province_id",new IntegerValue(BigInteger.valueOf(capital))) || NativeActionSteps.retreating(enemy)
                        || !(route.items().isEmpty() && nil(enemy,"move_target_province_id") || !route.items().isEmpty() && route.items().getLast().equals(enemy.get("move_target_province_id")))) return Optional.empty();
            } else if (!nil(enemy,"move_target_province_id") && !positive(enemy.get("move_target_province_id"))) return Optional.empty();
            ids.add(idAt(enemy,"army_id"));
        }
        if (new HashSet<>(ids).size() != ids.size()) return Optional.empty();
        return Optional.of(ids.stream().sorted().toList());
    }
    private static boolean scoreInside(Obj war,int lower,int upper) {
        return number(war.get("player_relative_war_score")).filter(v -> v.compareTo(BigInteger.valueOf(lower)) > 0 && v.compareTo(BigInteger.valueOf(upper)) < 0).isPresent();
    }
}
