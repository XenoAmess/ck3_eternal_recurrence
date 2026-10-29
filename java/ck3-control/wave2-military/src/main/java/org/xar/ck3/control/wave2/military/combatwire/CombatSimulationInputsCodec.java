package org.xar.ck3.control.wave2.military.combatwire;

import static org.xar.ck3.control.wave2.military.combatwire.CombatWire.*;
import static org.xar.ck3.control.wave2.military.combatwire.CombatOptionalLeaves.Leaf.*;
import static org.xar.ck3.control.wave2.military.combatwire.CombatSimulationInputs.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.wave2.military.combatwire.CombatEncounterScope.Coalition;
import org.xar.ck3.control.wave2.military.combatwire.CombatEncounterScope.ScopeRole;

/** Complete base v2 runtime validation; never grants Monte Carlo or active-combat readiness. */
public final class CombatSimulationInputsCodec {
    public static final List<String> SIMULATOR_GAPS=List.of("damage_to_casualty_allocation","pursuit_transition","battle_end_and_retreat_transition","phase_event_rng_and_effects");
    private static final Set<String> INPUT_GAPS=Set.of("target_terrain","crossing","attacker_defender_holding","contact_combat_width","army_identity_and_owner","commander_and_roll_bounds","regiment_composition","regiment_identity","regiment_maa_type","regiment_kind_and_main_phase_eligibility","effective_regiment_stats","counter_operands","knights","ongoing_combat_context","counter_resolutions");
    private static final String POLICY="explicit_hypothetical_fixed_at_contact_no_reinforcements";
    private static final Set<String> ROOT_OPTIONAL=Set.of("contextual_advantage",PHASE_EVENT_CALENDAR.wireName(),PHASE_EVENT_ROLE_COMPATIBILITY.wireName(),PHASE_EVENT_COMMANDER_SIDE_IDENTITY.wireName(),PHASE_EVENT_COMMANDER_TRIGGER.wireName(),PHASE_EVENT_COMMANDER_CHANCE.wireName(),KNIGHT_STAT_CONSUMPTION.wireName());
    private final CombatOptionalLeaves leaves;
    public CombatSimulationInputsCodec(CombatOptionalLeaves leaves){this.leaves=Objects.requireNonNull(leaves);}
    public CombatSimulationInputsCodec(){this(CombatOptionalLeaves.complete());}
    private static Status typedStatus(String value){return Status.valueOf(value.toUpperCase(java.util.Locale.ROOT));}
    private static Integer intValue(JsonNode value){return nil(value)?null:value.intValue();}
    private static Long longValue(JsonNode value){return nil(value)?null:value.longValue();}
    private static Boolean boolValue(JsonNode value){return nil(value)?null:value.booleanValue();}
    private static String stringValue(JsonNode value){return nil(value)?null:value.textValue();}
    private void leaf(ObjectNode parent,CombatOptionalLeaves.Leaf key,Integer character,String path,List<Army> armies,ObjectNode root){
        JsonNode normalized=leaves.normalize(key,parent.get(key.wireName()),new CombatOptionalLeaves.Context(path+"."+key.wireName(),character,armies,root));
        require(normalized!=null,"optional codec must return JSON null rather than Java null");parent.set(key.wireName(),normalized.deepCopy());
    }
    public CombatSimulationInputs normalize(JsonNode payload,CombatRequest request,CombatEncounterScope scope){
        Objects.requireNonNull(request);Objects.requireNonNull(scope);scope.verify(request);
        ObjectNode source=object(payload,Set.of("target_province_id","participant_policy","scenario","armies","target_province","ongoing_combats","counter_resolutions","completeness"),ROOT_OPTIONAL,"combat_simulation_inputs");
        ObjectNode root=source.deepCopy();int target=positive(root.get("target_province_id"),"combat_simulation_inputs.target_province_id");require(target==request.targetProvinceId(),"native combat target ProvinceID mismatch");
        eq(root.get("participant_policy"),POLICY,"native combat participant_policy is malformed");
        Scenario scenario=scenario(root.get("scenario"),request,scope);ArrayNode rawArmies=array(root.get("armies"),"combat_simulation_inputs.armies");
        require(rawArmies.size()==scope.selectedScope().size(),"native combat armies do not match the request");
        Set<String> gaps=new LinkedHashSet<>();Set<Integer> nativeIds=new HashSet<>(),regimentIds=new HashSet<>(),knightIds=new HashSet<>(),knightRegiments=new HashSet<>();List<Army> armies=new ArrayList<>();
        for(int i=0;i<rawArmies.size();i++){
            Army army=army(rawArmies.get(i),"combat_simulation_inputs.armies["+i+"]",target,scope.selectedScope().get(i),i<request.attackerArmyIds().size()?EncounterRole.ATTACKER:EncounterRole.DEFENDER,gaps,regimentIds,knightIds,knightRegiments);
            if(army.nativeCarmyId()!=null)require(nativeIds.add(army.nativeCarmyId()),"native combat armies repeat a CArmyID");armies.add(army);
        }
        TargetProvince targetProvince=target(root.get("target_province"),target,gaps);List<OngoingCombat> ongoing=ongoing(root.get("ongoing_combats"),gaps);
        Integer friendly=null,enemy=null;for(Army army:armies)if(army.owner().status()==Status.AVAILABLE){if(army.scopeRole().coalition()==Coalition.ENEMY){if(enemy==null)enemy=army.owner().characterId();}else if(friendly==null)friendly=army.owner().characterId();}
        List<CounterResolution> resolutions=resolutions(root.get("counter_resolutions"),gaps,friendly,enemy);int classCount=resolutions.get(0).classCount();
        for(Army army:armies)if(army.regiments()!=null)for(Regiment regiment:army.regiments()){Counter counter=regiment.counter();if(counter.status()==Status.AVAILABLE){require(counter.classIndex()<classCount,"native combat counter class_index is out of range");for(CounterTarget ct:counter.targets())require(ct.classIndex()<classCount,"native combat counter target is out of range");}}
        Completeness complete=completeness(root.get("completeness"),gaps);
        if(root.has("contextual_advantage"))root.set("contextual_advantage",ContextualAdvantageCodec.normalize(root.get("contextual_advantage"),target,scenario));
        for(var key:List.of(PHASE_EVENT_CALENDAR,PHASE_EVENT_ROLE_COMPATIBILITY,PHASE_EVENT_COMMANDER_SIDE_IDENTITY,PHASE_EVENT_COMMANDER_TRIGGER,PHASE_EVENT_COMMANDER_CHANCE))if(root.has(key.wireName()))leaf(root,key,null,"combat_simulation_inputs",armies,root);
        leaf(root,KNIGHT_STAT_CONSUMPTION,null,"combat_simulation_inputs",armies,root);
        return new CombatSimulationInputs(target,scenario,armies,targetProvince,ongoing,resolutions,complete,root);
    }
    private static Scenario scenario(JsonNode value,CombatRequest request,CombatEncounterScope scope){
        String name="combat_simulation_inputs.scenario";boolean ctor=request.constructorAdjacencyKindRaw()!=null;
        ObjectNode row=object(value,Set.of("kind","attacker_entry_province_id","attacker_army_ids","defender_army_ids","attacker_side","defender_side","attacker_position_policy","defender_position_policy","defender_insertion_order_policy","actual_route_dependency"),ctor?Set.of("contact_geometry_mode","constructor_adjacency_kind_raw"):Set.of(),name);
        require(!ctor||row.has("contact_geometry_mode")&&row.has("constructor_adjacency_kind_raw"),"native "+name+" schema is malformed");
        eq(row.get("kind"),"explicit_hypothetical_contact","native combat scenario kind is malformed");
        Integer entry;if(ctor){require(nil(row.get("attacker_entry_province_id"))&&i32(row.get("constructor_adjacency_kind_raw"),name+".constructor_adjacency_kind_raw")==0,"native defender constructor scenario binding is malformed");eq(row.get("contact_geometry_mode"),"native_defender_constructor_zero","native defender constructor scenario binding is malformed");entry=null;}
        else{entry=positive(row.get("attacker_entry_province_id"),name+".attacker_entry_province_id");require(entry.equals(request.attackerEntryProvinceId())&&entry!=request.targetProvinceId(),"native combat attacker entry ProvinceID mismatch");}
        List<Integer> a=ids(row.get("attacker_army_ids"),false,false,name+".attacker_army_ids"),d=ids(row.get("defender_army_ids"),false,false,name+".defender_army_ids");
        require(a.stream().noneMatch(d::contains),"native combat scenario repeats an ArmyID");require(a.equals(request.attackerArmyIds())&&d.equals(request.defenderArmyIds()),"native combat scenario participant partition drifted");
        Coalition as=Coalition.decode(row.get("attacker_side"),name+".attacker_side"),ds=Coalition.decode(row.get("defender_side"),name+".defender_side");require(as==scope.attackerSide()&&ds==scope.defenderSide()&&as!=ds,"native combat scenario coalition orientation drifted");
        eq(row.get("attacker_position_policy"),ctor?"fixed_at_target_hypothetical":"fixed_at_entry_hypothetical","native combat scenario position policy is malformed");eq(row.get("defender_position_policy"),"fixed_at_target_hypothetical","native combat scenario position policy is malformed");eq(row.get("defender_insertion_order_policy"),"explicit_request_order_hypothetical","native combat scenario position policy is malformed");require(!bool(row.get("actual_route_dependency"),name+".actual_route_dependency"),"native combat scenario position policy is malformed");
        return new Scenario(entry,a,d,as,ds,ctor);
    }
    private Army army(JsonNode value,String name,int target,CombatEncounterScope.ScopeRow expected,EncounterRole role,Set<String> gaps,Set<Integer> seenRegiments,Set<Integer> seenKnights,Set<Integer> seenKnightRegiments){
        ObjectNode row=object(value,"status army_id encounter_role native_carmy_id scope_role war_ids current_province_id owner commander regiments knights unavailable_reason",name);String status=statusAndReason(row,false,name);
        int id=nonnegative(row.get("army_id"),name+".army_id");require(id==expected.armyId(),"native "+name+".army_id changed request order");eq(row.get("encounter_role"),role==EncounterRole.ATTACKER?"attacker":"defender","native "+name+".encounter_role is malformed");
        ScopeRole scopeRole=ScopeRole.decode(row.get("scope_role"),name+".scope_role");require(scopeRole==expected.scopeRole(),"native "+name+".scope_role is malformed");List<Integer> wars=ids(row.get("war_ids"),true,false,name+".war_ids");require(wars.equals(expected.warIds()),"native "+name+".war_ids drifted from paused scope");
        Integer nativeId=optionalInt(row.get("native_carmy_id"),true,name+".native_carmy_id"),province=optionalInt(row.get("current_province_id"),true,name+".current_province_id");
        Owner owner=owner(row.get("owner"),name+".owner");Commander commander=commander(row.get("commander"),name+".commander",target);List<Regiment> regiments=null;
        if(nil(row.get("regiments")))gaps.add("regiment_composition");else{regiments=new ArrayList<>();ArrayNode raw=array(row.get("regiments"),name+".regiments");for(int i=0;i<raw.size();i++){Regiment regiment=regiment(raw.get(i),name+".regiments["+i+"]",target,province,gaps);require(seenRegiments.add(regiment.regimentId()),"native combat repeats a RegimentID");regiments.add(regiment);}}
        Set<Integer> ids=new HashSet<>();if(regiments!=null)for(Regiment regiment:regiments)ids.add(regiment.regimentId());Knights knights=knights(row.get("knights"),name+".knights",nativeId,ids,gaps,seenKnights,seenKnightRegiments);
        if(!status.equals("available")||nativeId==null||owner.status()!=Status.AVAILABLE)gaps.add("army_identity_and_owner");if(commander.status()==Status.UNAVAILABLE||commander.battleContext().status()!=Status.AVAILABLE)gaps.add("commander_and_roll_bounds");
        require(!status.equals("available")||nativeId!=null&&regiments!=null,"native available "+name+" is incomplete");
        return new Army(typedStatus(status),id,role,nativeId,scopeRole,wars,province,owner,commander,regiments,knights,stringValue(row.get("unavailable_reason")));
    }
    private static Owner owner(JsonNode value,String name){
        ObjectNode row=object(value,"status character_id counter_efficiency_raw counter_resistance_raw scale unavailable_reason",name);String status=statusAndReason(row,false,name);boolean available=status.equals("available");
        conditionalField(row,"character_id",available,32,true,false,name);for(String field:List.of("counter_efficiency_raw","counter_resistance_raw"))conditionalField(row,field,available,64,false,false,name);scale(row.get("scale"),name+".scale");
        return new Owner(typedStatus(status),intValue(row.get("character_id")),longValue(row.get("counter_efficiency_raw")),longValue(row.get("counter_resistance_raw")),stringValue(row.get("unavailable_reason")));
    }
    private Commander commander(JsonNode value,String name,int target){
        ObjectNode row=object(value,Set.of("status","character_id","generic_advantage_points","battle_context","unavailable_reason"),Set.of(PHASE_RITE_PARAMETERS.wireName()),name);String status=statusAndReason(row,true,name);boolean available=status.equals("available");
        conditionalField(row,"character_id",available,32,true,false,name);conditionalField(row,"generic_advantage_points",available,32,false,false,name);
        ObjectNode context=object(row.get("battle_context"),"status source_target_province_id effective_min_roll effective_max_roll unavailable_reason",name+".battle_context");String cs=statusAndReason(context,false,name+".battle_context");boolean ca=cs.equals("available");
        conditionalField(context,"source_target_province_id",ca,32,true,true,name+".battle_context");conditionalField(context,"effective_min_roll",ca,32,false,false,name+".battle_context");conditionalField(context,"effective_max_roll",ca,32,false,false,name+".battle_context");
        require(!ca||intValue(context.get("source_target_province_id"))==target,"native "+name+".battle_context target mismatch");require(!status.equals("absent")||!ca||intValue(context.get("effective_min_roll"))==0&&intValue(context.get("effective_max_roll"))==0,"native absent commander must have 0..0 roll bounds");
        leaf(row,PHASE_RITE_PARAMETERS,intValue(row.get("character_id")),name,List.of(),null);
        return new Commander(typedStatus(status),intValue(row.get("character_id")),intValue(row.get("generic_advantage_points")),new BattleContext(typedStatus(cs),intValue(context.get("source_target_province_id")),intValue(context.get("effective_min_roll")),intValue(context.get("effective_max_roll")),stringValue(context.get("unavailable_reason"))),stringValue(row.get("unavailable_reason")));
    }
    private Regiment regiment(JsonNode value,String name,int target,Integer currentProvince,Set<String> gaps){
        ObjectNode row=object(value,Set.of("status","regiment_id","identity_valid","current_soldiers","maximum_soldiers","maa_type","kind","fights_in_main_phase","effective_stats","counter","unavailable_reason"),Set.of("initialization_context_stats",ORDINARY_STAT_INPUTS.wireName(),MAA_STAT_INPUTS.wireName()),name);
        String status=statusAndReason(row,false,name);int id=positive(row.get("regiment_id"),name+".regiment_id");boolean identity=bool(row.get("identity_valid"),name+".identity_valid");int current=nonnegative(row.get("current_soldiers"),name+".current_soldiers"),max=nonnegative(row.get("maximum_soldiers"),name+".maximum_soldiers");
        ObjectNode maa=object(row.get("maa_type"),"status key unavailable_reason",name+".maa_type");String ms=statusAndReason(maa,true,name+".maa_type");if(ms.equals("available"))text(maa.get("key"),name+".maa_type.key");else require(nil(maa.get("key")),"native "+name+".maa_type.key must be null");
        ObjectNode kind=object(row.get("kind"),"status value unavailable_reason",name+".kind");String ks=statusAndReason(kind,false,name+".kind");if(ks.equals("available")){token(kind.get("value"),name+".kind.value","levy","men_at_arms");bool(row.get("fights_in_main_phase"),name+".fights_in_main_phase");}else{require(nil(kind.get("value")),"native "+name+".kind.value must be null");require(nil(row.get("fights_in_main_phase")),"native "+name+".fights_in_main_phase must be null when kind is not available");}
        EffectiveStats stats=stats(row.get("effective_stats"),name+".effective_stats",target);Counter counter=counter(row.get("counter"),name+".counter");
        if(!identity)gaps.add("regiment_identity");if(ms.equals("unavailable"))gaps.add("regiment_maa_type");if(!ks.equals("available"))gaps.add("regiment_kind_and_main_phase_eligibility");if(stats.status()!=Status.AVAILABLE)gaps.add("effective_regiment_stats");if(counter.status()==Status.UNAVAILABLE)gaps.add("counter_operands");
        boolean required=identity&&!ms.equals("unavailable")&&ks.equals("available")&&stats.status()==Status.AVAILABLE;require(!status.equals("available")||required,"native available "+name+" has unavailable required fields");require(!status.equals("unavailable")||!required||counter.status()==Status.UNAVAILABLE,"native unavailable "+name+" lacks a matching required-input gap");
        if(row.has("initialization_context_stats"))stats(row.get("initialization_context_stats"),name+".initialization_context_stats",currentProvince);
        for(var key:List.of(ORDINARY_STAT_INPUTS,MAA_STAT_INPUTS))if(row.has(key.wireName()))leaf(row,key,null,name,List.of(),null);
        RegimentKind rk=ks.equals("available")?(stringValue(kind.get("value")).equals("levy")?RegimentKind.LEVY:RegimentKind.MEN_AT_ARMS):null;
        return new Regiment(typedStatus(status),id,identity,current,max,new MaaType(typedStatus(ms),stringValue(maa.get("key")),stringValue(maa.get("unavailable_reason"))),new Kind(typedStatus(ks),rk,stringValue(kind.get("unavailable_reason"))),boolValue(row.get("fights_in_main_phase")),stats,counter,stringValue(row.get("unavailable_reason")));
    }
    private static EffectiveStats stats(JsonNode value,String name,Integer target){
        ObjectNode row=object(value,"status source_target_province_id max_size siege_value_raw damage_raw toughness_raw pursuit_raw screen_raw scale unavailable_reason",name);String status=statusAndReason(row,false,name);boolean available=status.equals("available");
        conditionalField(row,"source_target_province_id",available,32,true,true,name);require(!available||Objects.equals(intValue(row.get("source_target_province_id")),target),"native "+name+" target ProvinceID mismatch");conditionalField(row,"max_size",available,32,true,false,name);
        for(String field:List.of("siege_value_raw","damage_raw","toughness_raw","pursuit_raw","screen_raw"))conditionalField(row,field,available,64,false,false,name);scale(row.get("scale"),name+".scale");
        return new EffectiveStats(typedStatus(status),intValue(row.get("source_target_province_id")),intValue(row.get("max_size")),longValue(row.get("siege_value_raw")),longValue(row.get("damage_raw")),longValue(row.get("toughness_raw")),longValue(row.get("pursuit_raw")),longValue(row.get("screen_raw")),stringValue(row.get("unavailable_reason")));
    }
    private static Counter counter(JsonNode value,String name){
        ObjectNode row=object(value,"status class_index current_chunk_raw targets scale unavailable_reason",name);String status=statusAndReason(row,true,name);boolean available=status.equals("available");
        conditionalField(row,"class_index",available,32,true,false,name);conditionalField(row,"current_chunk_raw",available,64,true,false,name);List<CounterTarget> targets=null;
        if(status.equals("unavailable"))require(nil(row.get("targets")),"native "+name+".targets must be null");else{targets=new ArrayList<>();ArrayNode raw=array(row.get("targets"),name+".targets");for(int i=0;i<raw.size();i++){String tn=name+".targets["+i+"]";ObjectNode t=object(raw.get(i),"class_index effectiveness_raw scale",tn);targets.add(new CounterTarget(nonnegative(t.get("class_index"),tn+".class_index"),i64(t.get("effectiveness_raw"),tn+".effectiveness_raw")));scale(t.get("scale"),tn+".scale");}require(!status.equals("absent")||targets.isEmpty(),"native absent "+name+" must have no targets");}
        scale(row.get("scale"),name+".scale");return new Counter(typedStatus(status),intValue(row.get("class_index")),longValue(row.get("current_chunk_raw")),targets,stringValue(row.get("unavailable_reason")));
    }

    private Knights knights(JsonNode value,String name,Integer nativeArmy,Set<Integer> regiments,Set<String> gaps,Set<Integer> seenCharacters,Set<Integer> seenRegiments){
        ObjectNode row=object(value,Set.of("status","members","unavailable_reason"),Set.of("loaded_damage_multiplier","loaded_toughness_multiplier"),name);
        boolean damagePublished=row.has("loaded_damage_multiplier"),toughnessPublished=row.has("loaded_toughness_multiplier");Integer dm=damagePublished&&!nil(row.get("loaded_damage_multiplier"))?i32(row.get("loaded_damage_multiplier"),name+".loaded_damage_multiplier"):null,tm=toughnessPublished&&!nil(row.get("loaded_toughness_multiplier"))?i32(row.get("loaded_toughness_multiplier"),name+".loaded_toughness_multiplier"):null;
        String status=statusAndReason(row,false,name);List<Knight> members=null;
        if(status.equals("unavailable")){require(nil(row.get("members")),"native "+name+".members must be null");gaps.add("knights");}
        else{
            members=new ArrayList<>();ArrayNode raw=array(row.get("members"),name+".members");Knight previous=null;
            for(int i=0;i<raw.size();i++){
                String mn=name+".members["+i+"]";ObjectNode member=object(raw.get(i),Set.of("eligible","character_id","source_regiment_id","army_id","participant_army_membership_verified","prowess","knight_effectiveness_raw","effective_damage_raw","effective_toughness_raw","scale"),
                    Set.of("effectiveness_components","effectiveness_context",PHASE_RITE_PARAMETERS.wireName(),PHASE_WARMONGER_CORE.wireName(),PHASE_BERSERKER_VALIDITY.wireName(),PHASE_BERSERKER_CHANCE.wireName()),mn);
                require(bool(member.get("eligible"),mn+".eligible")&&bool(member.get("participant_army_membership_verified"),mn+".participant_army_membership_verified"),"native "+mn+" is not an eligible member");
                int character=nonnegative(member.get("character_id"),mn+".character_id"),regiment=positive(member.get("source_regiment_id"),mn+".source_regiment_id"),army=positive(member.get("army_id"),mn+".army_id");
                require(nativeArmy!=null&&army==nativeArmy,"native "+mn+".army_id is not its CArmyID");require(regiments.contains(regiment),"native "+mn+" is outside its army regiments");require(seenCharacters.add(character),"native combat repeats a knight CharacterID");require(seenRegiments.add(regiment),"native combat repeats a knight RegimentID");
                int prowess=i32(member.get("prowess"),mn+".prowess");long effectiveness=nonnegative64(member.get("knight_effectiveness_raw"),mn+".knight_effectiveness_raw"),damage=nonnegative64(member.get("effective_damage_raw"),mn+".effective_damage_raw"),toughness=nonnegative64(member.get("effective_toughness_raw"),mn+".effective_toughness_raw");
                Integer actualDm=!damagePublished&&!toughnessPublished?50:dm,actualTm=!damagePublished&&!toughnessPublished?10:tm;
                if(actualDm!=null&&actualTm!=null){BigInteger factor=BigInteger.valueOf(Math.max(1,prowess)).multiply(BigInteger.valueOf(effectiveness));require(BigInteger.valueOf(damage).equals(factor.multiply(BigInteger.valueOf(actualDm)))&&BigInteger.valueOf(toughness).equals(factor.multiply(BigInteger.valueOf(actualTm))),"native "+mn+" knight stats disagree");}
                scale(member.get("scale"),mn+".scale");for(var key:List.of(PHASE_RITE_PARAMETERS,PHASE_WARMONGER_CORE,PHASE_BERSERKER_VALIDITY,PHASE_BERSERKER_CHANCE))leaf(member,key,character,mn,List.of(),null);
                if(member.has("effectiveness_components")){String cn=mn+".effectiveness_components";ObjectNode c=object(member.get("effectiveness_components"),"status modifier_raw operand_raw",cn);status(c,false,cn);for(String field:List.of("modifier_raw","operand_raw"))nine(c.get(field),cn+"."+field);}
                if(member.has("effectiveness_context"))effectivenessContext(member.get("effectiveness_context"),mn+".effectiveness_context");
                Knight current=new Knight(character,regiment,army,prowess,effectiveness,damage,toughness);if(previous!=null)require(previous.armyId()<army||previous.armyId()==army&&(previous.sourceRegimentId()<regiment||previous.sourceRegimentId()==regiment&&previous.characterId()<=character),"native "+name+".members ordering is unstable");previous=current;members.add(current);
            }
        }
        return new Knights(typedStatus(status),members,dm,tm,damagePublished,toughnessPublished,stringValue(row.get("unavailable_reason")));
    }
    private static void nine(JsonNode value,String name){ArrayNode a=array(value,name);require(a.size()==9,"native "+name+" must have nine values");for(int i=0;i<a.size();i++)i64(a.get(i),name+"["+i+"]");}
    private void effectivenessContext(JsonNode value,String name){
        ObjectNode row=object(value,Set.of("schema","status","character_id","modifier_indices","modifier_raw","operand_raw","scale","unavailable_reason"),Set.of(KNIGHT_CURRENT_MODEL_ASSOCIATION.wireName()),name);
        eq(row.get("schema"),"ck3_12003_knight_effectiveness_context_v1","native "+name+".schema is malformed");String status=statusAndReason(row,false,name);Integer character=optionalInt(row.get("character_id"),false,name+".character_id");require(!status.equals("available")||character!=null,"native "+name+".character_id is missing");
        ArrayNode indices=array(row.get("modifier_indices"),name+".modifier_indices");require(indices.size()==9,"native "+name+".modifier_indices is malformed");for(int i=0;i<9;i++)require(i32(indices.get(i),name+".modifier_indices["+i+"]")==0xc1+i,"native "+name+".modifier_indices is malformed");
        for(String field:List.of("modifier_raw","operand_raw"))if(status.equals("unavailable"))require(nil(row.get(field)),"native "+name+"."+field+" must be null");else nine(row.get(field),name+"."+field);
        scale(row.get("scale"),name+".scale");if(row.has(KNIGHT_CURRENT_MODEL_ASSOCIATION.wireName()))leaf(row,KNIGHT_CURRENT_MODEL_ASSOCIATION,character,name,List.of(),null);
    }
    private static TargetProvince target(JsonNode value,int target,Set<String> gaps){
        String name="combat_simulation_inputs.target_province";ObjectNode row=object(value,"status province_id terrain crossing defender_context precontact_width unavailable_reason",name);String status=statusAndReason(row,false,name);int province=positive(row.get("province_id"),name+".province_id");require(province==target,"native target_province identity mismatch");
        String tn=name+".terrain";ObjectNode terrain=object(row.get("terrain"),"status key combat_width_multiplier_raw scale unavailable_reason",tn);String ts=statusAndReason(terrain,false,tn);boolean ta=ts.equals("available");if(ta)text(terrain.get("key"),tn+".key");else require(nil(terrain.get("key")),"native "+tn+".key must be null");conditionalField(terrain,"combat_width_multiplier_raw",ta,64,false,false,tn);scale(terrain.get("scale"),tn+".scale");
        String cn=name+".crossing";ObjectNode crossing=object(row.get("crossing"),"status kind unavailable_reason",cn);String cs=statusAndReason(crossing,false,cn);if(cs.equals("available"))token(crossing.get("kind"),cn+".kind","none","river","large_river","strait");else require(nil(crossing.get("kind")),"native "+cn+".kind must be null");
        String dn=name+".defender_context";ObjectNode defender=object(row.get("defender_context"),"status defender_side holding_defender_status holding_defender holding_unavailable_reason unavailable_reason",dn);String ds=statusAndReason(defender,false,dn),hs=token(defender.get("holding_defender_status"),dn+".holding_defender_status","available","unavailable");Coalition side=null;
        if(ds.equals("available"))side=Coalition.decode(defender.get("defender_side"),dn+".defender_side");else require(nil(defender.get("defender_side")),"native unavailable "+dn+" must null defender_side");
        if(hs.equals("available")){require(ds.equals("available"),"native unavailable "+dn+" cannot publish holding context");bool(defender.get("holding_defender"),dn+".holding_defender");}else require(nil(defender.get("holding_defender")),"native unavailable "+dn+".holding_defender must be null");
        String holdingReason=reason(hs,defender.get("holding_unavailable_reason"),dn+".holding");
        String wn=name+".precontact_width";ObjectNode width=object(row.get("precontact_width"),"status base final unavailable_reason",wn);String ws=statusAndReason(width,false,wn);conditionalField(width,"base",ws.equals("available"),32,true,false,wn);conditionalField(width,"final",ws.equals("available"),32,true,false,wn);
        if(!status.equals("available")||!ta)gaps.add("target_terrain");if(!cs.equals("available"))gaps.add("crossing");if(!ds.equals("available")||!hs.equals("available"))gaps.add("attacker_defender_holding");if(!ws.equals("available"))gaps.add("contact_combat_width");require(!status.equals("available")||ta,"native available target_province lacks terrain");
        return new TargetProvince(typedStatus(status),province,new Terrain(typedStatus(ts),stringValue(terrain.get("key")),longValue(terrain.get("combat_width_multiplier_raw")),stringValue(terrain.get("unavailable_reason"))),new Crossing(typedStatus(cs),stringValue(crossing.get("kind")),stringValue(crossing.get("unavailable_reason"))),new DefenderContext(typedStatus(ds),side,typedStatus(hs),boolValue(defender.get("holding_defender")),holdingReason,stringValue(defender.get("unavailable_reason"))),new Width(typedStatus(ws),intValue(width.get("base")),intValue(width.get("final")),stringValue(width.get("unavailable_reason"))),stringValue(row.get("unavailable_reason")));
    }
    private static List<OngoingCombat> ongoing(JsonNode value,Set<String> gaps){
        ArrayNode raw=array(value,"combat_simulation_inputs.ongoing_combats");Set<Integer> seen=new HashSet<>();List<OngoingCombat> result=new ArrayList<>();
        for(int i=0;i<raw.size();i++){
            String name="combat_simulation_inputs.ongoing_combats["+i+"]";ObjectNode row=object(raw.get(i),"status combat_id province_id phase phase_day base_combat_width final_combat_width side_0_roll side_1_roll base_advantage resolved_advantage orientation unavailable_reason",name);String status=statusAndReason(row,false,name);boolean a=status.equals("available");
            Integer id=nil(row.get("combat_id"))?null:i32(row.get("combat_id"),name+".combat_id");require(!a||id!=null&&id!=-1,"native available "+name+".combat_id is invalid");if(id!=null)require(seen.add(id),"native ongoing_combats repeats a CombatID");
            conditionalField(row,"province_id",a,32,true,true,name);for(String field:List.of("phase","phase_day","base_combat_width","final_combat_width"))conditionalField(row,field,a,32,true,false,name);require(nil(row.get("phase"))||intValue(row.get("phase"))<=3,"native "+name+".phase is out of range");
            for(String field:List.of("side_0_roll","side_1_roll"))conditionalField(row,field,a,32,false,false,name);for(String field:List.of("base_advantage","resolved_advantage"))conditionalField(row,field,a,64,false,false,name);
            if(a)eq(row.get("orientation"),"native_side_0_attacker_side_1_defender","native "+name+".orientation is malformed");else{require(nil(row.get("orientation")),"native unavailable "+name+" must null orientation");gaps.add("ongoing_combat_context");}
            result.add(new OngoingCombat(typedStatus(status),id,intValue(row.get("province_id")),intValue(row.get("phase")),intValue(row.get("phase_day")),intValue(row.get("base_combat_width")),intValue(row.get("final_combat_width")),intValue(row.get("side_0_roll")),intValue(row.get("side_1_roll")),longValue(row.get("base_advantage")),longValue(row.get("resolved_advantage")),stringValue(row.get("orientation")),stringValue(row.get("unavailable_reason"))));
        }return List.copyOf(result);
    }
    private static List<CounterResolution> resolutions(JsonNode value,Set<String> gaps,Integer friendly,Integer enemy){
        ArrayNode raw=array(value,"combat_simulation_inputs.counter_resolutions");require(raw.size()==2,"native combat must publish two counter resolutions");List<CounterResolution> result=new ArrayList<>();Integer common=null;
        for(int i=0;i<2;i++){
            String name="combat_simulation_inputs.counter_resolutions["+i+"]";ObjectNode row=object(raw.get(i),"status countered_side countering_side countered_modifier_owner_character_id countering_modifier_owner_character_id context_scale_raw class_count damage_retention_by_class_raw scale unavailable_reason",name);String status=statusAndReason(row,false,name);boolean a=status.equals("available");
            Coalition countered=Coalition.decode(row.get("countered_side"),name+".countered_side"),countering=Coalition.decode(row.get("countering_side"),name+".countering_side");require(countered==(i==0?Coalition.PLAYER_OR_ALLIED:Coalition.ENEMY)&&countering!=(countered),"native "+name+" side orientation is malformed");
            conditionalField(row,"countered_modifier_owner_character_id",a,32,true,false,name);conditionalField(row,"countering_modifier_owner_character_id",a,32,true,false,name);conditionalField(row,"context_scale_raw",a,64,true,false,name);
            Integer co=intValue(row.get("countered_modifier_owner_character_id")),cg=intValue(row.get("countering_modifier_owner_character_id"));require(!a||Objects.equals(co,i==0?friendly:enemy)&&Objects.equals(cg,i==0?enemy:friendly),"native "+name+" did not use the first request-order owner");
            int count=positive(row.get("class_count"),name+".class_count");require(common==null||common==count,"native counter resolutions disagree on class_count");common=count;List<Long> retention=null;
            if(a){ArrayNode vec=array(row.get("damage_retention_by_class_raw"),name+".damage_retention_by_class_raw");retention=new ArrayList<>();for(int j=0;j<vec.size();j++){long n=nonnegative64(vec.get(j),name+".damage_retention_by_class_raw["+j+"]");require(n<=100000,"native "+name+" retention is out of range");retention.add(n);}require(retention.size()==count,"native "+name+" retention vector is incomplete");}
            else{require(nil(row.get("damage_retention_by_class_raw")),"native unavailable "+name+" must null retention");gaps.add("counter_resolutions");}
            scale(row.get("scale"),name+".scale");result.add(new CounterResolution(typedStatus(status),countered,countering,co,cg,longValue(row.get("context_scale_raw")),count,retention,stringValue(row.get("unavailable_reason"))));
        }return List.copyOf(result);
    }
    private static Completeness completeness(JsonNode value,Set<String> gaps){
        String name="combat_simulation_inputs.completeness";ObjectNode row=object(value,"observation_slice input_observation_ready monte_carlo_ready missing_required_domains",name);eq(row.get("observation_slice"),"precontact-composition-context-v2","native combat observation_slice is malformed");
        boolean ready=bool(row.get("input_observation_ready"),name+".input_observation_ready"),mc=bool(row.get("monte_carlo_ready"),name+".monte_carlo_ready");require(!mc,"combat-simulation-inputs-v2 cannot be Monte Carlo ready");List<String> domains=strings(row.get("missing_required_domains"),name+".missing_required_domains");
        require(new HashSet<>(domains).size()==domains.size(),"native combat missing_required_domains has duplicates");require(domains.size()>=SIMULATOR_GAPS.size()&&domains.subList(domains.size()-SIMULATOR_GAPS.size(),domains.size()).equals(SIMULATOR_GAPS),"native combat simulator gaps are malformed");
        List<String> observed=domains.subList(0,domains.size()-SIMULATOR_GAPS.size());require(INPUT_GAPS.containsAll(observed),"native combat input gap is not part of v1");require(new HashSet<>(observed).equals(gaps),"native combat completeness disagrees with subdomains");require(ready==gaps.isEmpty(),"native combat input_observation_ready is inconsistent");require(!ready||domains.equals(SIMULATOR_GAPS),"available combat input has non-simulator gaps");return new Completeness(ready,false,domains);
    }
}

