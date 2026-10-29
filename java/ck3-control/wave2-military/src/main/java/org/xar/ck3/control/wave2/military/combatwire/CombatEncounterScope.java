package org.xar.ck3.control.wave2.military.combatwire;

import static org.xar.ck3.control.wave2.military.combatwire.CombatWire.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Selected published scope; no ownership/position inference is admitted. */
public record CombatEncounterScope(List<ScopeRow> selectedScope, Coalition attackerSide,
        Coalition defenderSide, List<Integer> commonWarIds) {
    public enum Coalition {
        PLAYER_OR_ALLIED("player_or_allied"), ENEMY("enemy");
        private final String wireName; Coalition(String value){wireName=value;} public String wireName(){return wireName;}
        public static Coalition decode(JsonNode value,String name){String raw=token(value,name,"player_or_allied","enemy");return raw.equals("enemy")?ENEMY:PLAYER_OR_ALLIED;}
    }
    public enum ScopeRole {
        ACTIVE_WAR_ENEMY("active_war_enemy",0), ACTIVE_WAR_ALLY("active_war_ally",1), PLAYER("player",2);
        private final String wireName; private final int precedence;
        ScopeRole(String value,int rank){wireName=value;precedence=rank;} public String wireName(){return wireName;}
        public Coalition coalition(){return this==ACTIVE_WAR_ENEMY?Coalition.ENEMY:Coalition.PLAYER_OR_ALLIED;}
        public static ScopeRole decode(JsonNode value,String name){String raw=token(value,name,"player","active_war_ally","active_war_enemy");for(var role:values())if(role.wireName.equals(raw))return role;throw new IllegalStateException();}
    }
    public record ScopeRow(int armyId,ScopeRole scopeRole,List<Integer> warIds) {
        public ScopeRow { require(armyId>=0,"invalid public CUnit");Objects.requireNonNull(scopeRole);warIds=List.copyOf(warIds);HashSet<Integer> seen=new HashSet<>();for(Integer id:warIds)require(id!=null&&id>0&&seen.add(id),"invalid or duplicate WarID"); }
        public ObjectNode toJson(){ObjectNode row=empty().put("army_id",armyId).put("scope_role",scopeRole.wireName());row.set("war_ids",jsonIds(warIds));return row;}
    }
    public CombatEncounterScope {
        selectedScope=List.copyOf(selectedScope);commonWarIds=List.copyOf(commonWarIds);
        require(!selectedScope.isEmpty()&&attackerSide!=null&&defenderSide!=null&&attackerSide!=defenderSide&&!commonWarIds.isEmpty(),"invalid encounter coalitions or common war");
        HashSet<Integer> ids=new HashSet<>();for(var row:selectedScope) require(ids.add(row.armyId()),"repeated public CUnit");
        HashSet<Integer> wars=new HashSet<>();for(Integer id:commonWarIds)require(id!=null&&id>0&&wars.add(id),"invalid common WarID");
    }
    public void verify(CombatRequest request) {
        require(selectedScope.stream().map(ScopeRow::armyId).toList().equals(request.armyIds()),"expected combat encounter scope is malformed");
        for(int i=0;i<selectedScope.size();i++)require(selectedScope.get(i).scopeRole().coalition()==(i<request.attackerArmyIds().size()?attackerSide:defenderSide),"encounter partitions differ from published scope");
        List<Integer> common=new ArrayList<>(selectedScope.get(0).warIds());for(var row:selectedScope)common.removeIf(id->!row.warIds().contains(id));
        require(common.equals(commonWarIds),"common WarIDs differ from selected published scope");
    }
    public ObjectNode toJson(CombatRequest request){
        verify(request);ObjectNode root=empty();root.set("army_ids",jsonIds(request.armyIds()));root.set("attacker_army_ids",jsonIds(request.attackerArmyIds()));root.set("defender_army_ids",jsonIds(request.defenderArmyIds()));
        ArrayNode selected=root.putArray("selected_scope"),a=root.putArray("attacker_scope"),d=root.putArray("defender_scope");
        for(int i=0;i<selectedScope.size();i++){ScopeRow row=selectedScope.get(i);selected.add(row.toJson());(i<request.attackerArmyIds().size()?a:d).add(row.toJson());}
        root.put("attacker_side",attackerSide.wireName()).put("defender_side",defenderSide.wireName());root.set("common_war_ids",jsonIds(commonWarIds));return root;
    }
    public static CombatEncounterScope decode(JsonNode value,CombatRequest request){
        require(value instanceof ObjectNode,"expected combat encounter scope is malformed");List<ScopeRow> rows=new ArrayList<>();
        for(JsonNode raw:array(value.get("selected_scope"),"selected_scope")){require(raw instanceof ObjectNode,"expected scope row malformed");rows.add(new ScopeRow(nonnegative(raw.get("army_id"),"army_id"),ScopeRole.decode(raw.get("scope_role"),"scope_role"),ids(raw.get("war_ids"),true,false,"war_ids")));}
        CombatEncounterScope scope=new CombatEncounterScope(rows,Coalition.decode(value.get("attacker_side"),"attacker_side"),Coalition.decode(value.get("defender_side"),"defender_side"),ids(value.get("common_war_ids"),true,true,"common_war_ids"));scope.verify(request);return scope;
    }
    private record War(int id,List<Integer> members) { }
    /** Implements army_strength_scope's published order, precedence and full WarID union. */
    public static CombatEncounterScope fromSnapshot(JsonNode snapshot,CombatRequest request){
        require(snapshot instanceof ObjectNode,"army-strength scope requires snapshot");
        Map<Integer,ScopeRole> roles=new LinkedHashMap<>();Map<Integer,List<Integer>> warsByArmy=new LinkedHashMap<>();List<War> wars=new ArrayList<>();
        admit(array(snapshot.get("player_armies"),"player_armies"),ScopeRole.PLAYER,roles,warsByArmy);
        for(JsonNode war:array(snapshot.get("active_wars"),"active_wars")){
            require(war instanceof ObjectNode,"army-strength scope contains a malformed war");int id=positive(war.get("war_id"),"army-strength scope war_id");
            ArrayNode allied=array(war.get("allied_armies"),"allied_armies"),enemy=array(war.get("enemy_armies"),"enemy_armies");
            List<Integer> members=admit(allied,ScopeRole.ACTIVE_WAR_ALLY,roles,warsByArmy);members.addAll(admit(enemy,ScopeRole.ACTIVE_WAR_ENEMY,roles,warsByArmy));wars.add(new War(id,List.copyOf(members)));
        }
        for(var war:wars)for(int id:new HashSet<>(war.members())){List<Integer> ids=warsByArmy.get(id);if(!ids.contains(war.id()))ids.add(war.id());}
        List<ScopeRow> selected=new ArrayList<>();for(int id:request.armyIds()){require(roles.containsKey(id),"army_ids are outside the current published player/war scope: "+id);selected.add(new ScopeRow(id,roles.get(id),warsByArmy.get(id)));}
        List<Integer> common=new ArrayList<>(selected.get(0).warIds());for(var row:selected)common.removeIf(id->!row.warIds().contains(id));
        var scope=new CombatEncounterScope(selected,selected.get(0).scopeRole().coalition(),selected.get(request.attackerArmyIds().size()).scopeRole().coalition(),common);scope.verify(request);return scope;
    }
    private static List<Integer> admit(ArrayNode raw,ScopeRole role,Map<Integer,ScopeRole> roles,Map<Integer,List<Integer>> wars){
        List<Integer> result=new ArrayList<>();for(JsonNode army:raw){require(army instanceof ObjectNode,"army-strength scope contains a malformed army");int id=nonnegative(army.get("army_id"),"army-strength scope army_id");result.add(id);ScopeRole old=roles.get(id);if(old==null||role.precedence>old.precedence)roles.put(id,role);wars.computeIfAbsent(id,key->new ArrayList<>());}return result;
    }
}

