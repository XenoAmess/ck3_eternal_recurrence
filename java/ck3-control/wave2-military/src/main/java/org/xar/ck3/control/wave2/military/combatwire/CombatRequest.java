package org.xar.ck3.control.wave2.military.combatwire;

import static org.xar.ck3.control.wave2.military.combatwire.CombatWire.*;
import com.fasterxml.jackson.databind.JsonNode;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;

/** Validated caller-selected physical sides. Public CUnit zero is legal. */
public record CombatRequest(int targetProvinceId, Integer attackerEntryProvinceId,
        List<Integer> attackerArmyIds, List<Integer> defenderArmyIds, Integer constructorAdjacencyKindRaw) {
    public static final String CAPABILITY = "game.command.query-combat-simulation-inputs-v2-N";
    public static final String PREFIX = "query-combat-simulation-inputs-v2-";
    public CombatRequest {
        require(targetProvinceId > 0, "target_province_id must be a positive signed int32");
        require(constructorAdjacencyKindRaw == null || constructorAdjacencyKindRaw == 0, "constructor_adjacency_kind_raw supports only native defender raw0");
        if(constructorAdjacencyKindRaw == null) require(attackerEntryProvinceId != null && attackerEntryProvinceId > 0 && attackerEntryProvinceId != targetProvinceId, "attacker_entry_province_id must be positive and differ from target_province_id");
        else require(attackerEntryProvinceId == null,"constructor raw mode requires attacker_entry_province_id=null");
        require(attackerArmyIds != null && defenderArmyIds != null && !attackerArmyIds.isEmpty() && !defenderArmyIds.isEmpty(),"combat sides must be non-empty arrays");
        attackerArmyIds=List.copyOf(attackerArmyIds); defenderArmyIds=List.copyOf(defenderArmyIds);
        HashSet<Integer> seen = new HashSet<>();
        for (List<Integer> side:List.of(attackerArmyIds,defenderArmyIds)) for(Integer id:side) require(id != null && id >= 0 && seen.add(id),"combat participant ArmyIDs must be nonnegative signed32 without duplicates");
        require(seen.size() <= 64, "combat participants must contain at most 64 ArmyIDs");
    }
    public static CombatRequest decode(JsonNode target, JsonNode entry, JsonNode attackers, JsonNode defenders, JsonNode constructor) {
        Integer ctor = nil(constructor) ? null : i32(constructor,"constructor_adjacency_kind_raw");
        return new CombatRequest(positive(target,"target_province_id"), optionalInt(entry,true,"attacker_entry_province_id"),
            ids(attackers,false,true,"attacker_army_ids"), ids(defenders,false,true,"defender_army_ids"), ctor);
    }
    public String toStep() {
        List<String> tokens=new ArrayList<>(); tokens.add(Integer.toString(targetProvinceId)); tokens.add(attackerEntryProvinceId==null?"ctor0":attackerEntryProvinceId.toString()); tokens.add("a"); tokens.add(Integer.toString(attackerArmyIds.size()));
        attackerArmyIds.forEach(i->tokens.add(i.toString())); tokens.add("d"); tokens.add(Integer.toString(defenderArmyIds.size())); defenderArmyIds.forEach(i->tokens.add(i.toString()));
        return PREFIX+String.join("-",tokens);
    }
    public static Optional<CombatRequest> parseStep(String value) {
        if(value==null || !value.startsWith(PREFIX)) return Optional.empty();
        String[] t=value.substring(PREFIX.length()).split("-",-1);
        try {
            if(t.length<8 || !t[2].equals("a")) return Optional.empty();
            int target=canonical(t[0],true), ac=canonical(t[3],true);
            Integer entry=t[1].equals("ctor0")?null:canonical(t[1],true);
            require(ac<=64 && 4+ac+2<t.length && t[4+ac].equals("d"),"invalid partition");
            int dc=canonical(t[5+ac],true); require(dc<=64 && t.length==6+ac+dc,"invalid partition");
            List<Integer> a=new ArrayList<>(), d=new ArrayList<>();
            for(int i=0;i<ac;i++)a.add(canonical(t[4+i],false)); for(int i=0;i<dc;i++)d.add(canonical(t[6+ac+i],false));
            return Optional.of(new CombatRequest(target,entry,a,d,entry==null?0:null));
        } catch(IllegalArgumentException e) { return Optional.empty(); }
    }
    private static int canonical(String value,boolean positive) {
        require(value.matches(positive?"[1-9][0-9]*":"0|[1-9][0-9]*"),"noncanonical token"); return Integer.parseInt(value);
    }
    public List<Integer> armyIds() { List<Integer> all=new ArrayList<>(attackerArmyIds);all.addAll(defenderArmyIds);return List.copyOf(all); }
}

