package org.xar.ck3.control.application.battleadvance;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Original native_driver.py:31369-31493 compact historical tactical slice, shared with other date composites. */
public final class BattleWarProgress {
    private BattleWarProgress() { }
    public static Obj summary(Obj snapshot) {
        List<Value> wars = new ArrayList<>();
        for (Value item : array(snapshot.get("active_wars"), "active_wars")) {
            Obj war = object(item, "war"); var row = new LinkedHashMap<String, Value>();
            for (String key : List.of("war_id", "player_relative_war_score", "enemy_primary_default_raise_province_id")) row.put(key, nullable(war, key));
            Value objectives = war.get("war_objective_province_ids");
            row.put("war_objective_province_ids", objectives == null ? new Arr(List.of()) : new Arr(array(objectives, "war_objective_province_ids")));
            List<Value> active = new ArrayList<>();
            if (war.get("objective_province_states") instanceof Arr states) for (Value state : states.items())
                if (state instanceof Obj objective && objective.get("active_siege") instanceof Obj) active.add(state);
            row.put("objective_province_states", new Arr(active));
            row.put("player_armies", armies(war.get("allied_armies"), true)); row.put("enemy_armies", armies(war.get("enemy_armies"), false)); wars.add(new Obj(row));
        }
        return new Obj(Map.of("date_raw", nullable(snapshot, "date_raw"), "wars", new Arr(wars)));
    }
    private static Arr armies(Value value, boolean controllableOnly) {
        List<Obj> result = new ArrayList<>();
        if (value instanceof Arr rows) for (Value item : rows.items()) {
            if (!(item instanceof Obj army) || controllableOnly && !new Bool(true).equals(army.get("controllable"))) continue;
            var row = new LinkedHashMap<String, Value>();
            for (String key : List.of("army_id", "current_province_id", "soldiers", "move_target_province_id")) row.put(key, nullable(army, key));
            for (String key : List.of("in_combat", "retreating")) if (army.get(key) instanceof Bool) row.put(key, army.get(key));
            for (String key : List.of("army_state", "army_state_code")) if (army.get(key) instanceof Text || army.get(key) instanceof IntegerValue) row.put(key, army.get(key));
            for (String key : List.of("siege_days_left", "siege_province_holder_character_id", "siege_province_in_player_subrealm"))
                if (army.members().containsKey(key)) row.put(key, army.get(key));
            if (army.get("route_province_ids") instanceof Arr) row.put("route_province_ids", army.get("route_province_ids")); result.add(new Obj(row));
        }
        result.sort(Comparator.comparing(row -> row.get("army_id") instanceof IntegerValue id ? id.value() : BigInteger.valueOf(Integer.MAX_VALUE)));
        return new Arr(result.stream().<Value>map(row -> row).toList());
    }
    private static Value nullable(Obj object, String field) { return object.get(field) == null ? Nil.INSTANCE : object.get(field); }
}
