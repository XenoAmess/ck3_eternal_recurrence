package org.xar.ck3.control.wave2.military.combatwire;

import static org.xar.ck3.control.wave2.military.combatwire.CombatWire.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.wave2.military.combatwire.CombatSimulationInputs.Scenario;

/** Optional constructor observations remain scoped unavailable on malformed fragments. */
public final class ContextualAdvantageCodec {
    private ContextualAdvantageCodec(){ }
    private static final List<String> NONRELIGIOUS=List.of("attacker_adjacency","defender_adjacency","attacker_terrain","defender_terrain","supply_0","supply_1","holding_defender_1","gathering_army_0","gathering_army_1","debt_0_owner","debt_0_treasury","debt_1_owner","debt_1_treasury");
    private static final List<String> COMMANDER=List.of("effective_martial","opposing_primary_context","province_raw_context","army_gated_modifier","primary_identity_modifier","gathering_loaded_rule","commander_relation_aggregate");
    private static String side(String stage){
        return switch(stage){case "attacker_adjacency","attacker_terrain","supply_0","gathering_army_0","debt_0_owner","debt_0_treasury"->"attacker";default->"defender";};
    }
    private static void nullableI32(ObjectNode row,String key,String name){if(!nil(row.get(key)))i32(row.get(key),name+"."+key);}
    private static void nullableI64(ObjectNode row,String key,String name){if(!nil(row.get(key)))i64(row.get(key),name+"."+key);}
    private static void nullableBool(ObjectNode row,String key,String name){if(!nil(row.get(key)))bool(row.get(key),name+"."+key);}
    private static void nullableText(ObjectNode row,String key,String name){CombatWire.nullableText(row.get(key),name+"."+key);}
    private static void uint32(JsonNode value,String name,boolean nullable,boolean allowMax){
        if(nullable&&nil(value))return;long id=nonnegative64(value,name);require(id<=(allowMax?0xffffffffL:0xfffffffeL),"native "+name+" must be a nullable uint32 database ID");
    }
    private static BigInteger big(ObjectNode row,String key){return row.get(key).bigIntegerValue();}
    private static ObjectNode unavailable(int target,String reason,int version,boolean nonreligious){
        ObjectNode result=empty().put("schema_version",version).put("status","unavailable").put("scope",version==2?"hypothetical_constructor_context":"hypothetical_nonreligious_constructor_context").put("scale",100000).put("target_province_id",target);
        result.putNull("sides").putNull("base_nonreligious_accumulator_raw").putNull("synthetic_zero_roll_total_raw").putNull("synthetic_helper_total_match").put("partial_context_observation_ready",false).put("complete_encounter_advantage_ready",false).put("unavailable_reason",reason);result.putArray("missing_domains").add("religion_constructor_sources");
        if(version==2)result.put("religion_constructor_sources_ready",false).putNull("base_constructor_accumulator_raw").putNull("religion_constructor_sources");
        if(nonreligious)result.putNull("nonreligious_constructor_sources");return result;
    }
    public static ObjectNode normalize(JsonNode value,int target,Scenario scenario){
        String name="combat_simulation_inputs.contextual_advantage";int version=1;
        boolean nonreligious=value instanceof ObjectNode&&value.has("nonreligious_constructor_sources");
        try{
            if(value instanceof ObjectNode&&value.path("schema_version").isNumber()&&value.path("schema_version").decimalValue().compareTo(java.math.BigDecimal.valueOf(2))==0)version=2;
            Set<String> extra=new java.util.HashSet<>();if(version==2)extra.addAll(Set.of("religion_constructor_sources_ready","base_constructor_accumulator_raw","religion_constructor_sources"));if(nonreligious)extra.add("nonreligious_constructor_sources");
            ObjectNode row=object(value,Set.of("schema_version","status","scope","scale","target_province_id","sides","base_nonreligious_accumulator_raw","synthetic_zero_roll_total_raw","synthetic_helper_total_match","partial_context_observation_ready","complete_encounter_advantage_ready","missing_domains","unavailable_reason"),extra,name).deepCopy();
            version=i32(row.get("schema_version"),name+".schema_version");require(version==1||version==2,"native "+name+".schema_version must be 1 or 2");
            if(version==2)for(String key:List.of("religion_constructor_sources_ready","base_constructor_accumulator_raw","religion_constructor_sources"))require(row.has(key),"native "+name+" schema is malformed");
            String status=status(row,false,name);boolean available=status.equals("available");eq(row.get("scope"),version==2?"hypothetical_constructor_context":"hypothetical_nonreligious_constructor_context","native "+name+".scope is malformed");
            i32(row.get("scale"),name+".scale");scale(row.get("scale"),name+".scale");require(positive(row.get("target_province_id"),name+".target_province_id")==target,"native "+name+" target ProvinceID mismatch");
            require(bool(row.get("partial_context_observation_ready"),name+".partial_context_observation_ready")==available,"native "+name+" partial readiness is inconsistent");require(!bool(row.get("complete_encounter_advantage_ready"),name+".complete_encounter_advantage_ready"),"native "+name+" cannot be complete encounter ready");
            boolean religionReady=false;if(version==2){religionReady=bool(row.get("religion_constructor_sources_ready"),name+".religion_constructor_sources_ready");require(religionReady==available,"native "+name+" religion readiness is inconsistent");}
            require(strings(row.get("missing_domains"),name+".missing_domains").equals(religionReady?List.of():List.of("religion_constructor_sources")),"native "+name+" religion source gap is inconsistent");String reason=reason(status,row.get("unavailable_reason"),name);
            conditionalField(row,"base_nonreligious_accumulator_raw",available,64,false,false,name);conditionalField(row,"synthetic_zero_roll_total_raw",available,64,false,false,name);if(version==2)conditionalField(row,"base_constructor_accumulator_raw",available,64,false,false,name);
            if(!available){
                require(version!=2||nil(row.get("religion_constructor_sources")),"native unavailable "+name+" must null religion sources");require(!nonreligious||nil(row.get("nonreligious_constructor_sources")),"native unavailable "+name+" must null nonreligious sources");require(nil(row.get("sides"))&&nil(row.get("synthetic_helper_total_match")),"native unavailable "+name+" must null context values");return unavailable(target,reason,version,nonreligious);
            }
            require(bool(row.get("synthetic_helper_total_match"),name+".synthetic_helper_total_match"),"native "+name+" synthetic helper mismatch");ArrayNode sides=array(row.get("sides"),name+".sides");require(sides.size()==2,"native "+name+" must publish two ordered sides");
            for(int i=0;i<2;i++){
                String sn=name+".sides["+i+"]";ObjectNode sr=object(sides.get(i),Set.of("side_index","ordered_public_cunit_ids","selected_commander_character_id","relation_kind_raw","commander_dynamic_raw","side_dynamic_raw","target_conditionals_residual_raw","side_total_raw"),Set.of("side_modifier_sources","commander_source_inputs","commander_sources"),sn);
                require(i32(sr.get("side_index"),sn+".side_index")==i,"native "+sn+" side order mismatch");require(ids(sr.get("ordered_public_cunit_ids"),false,true,sn+".ordered_public_cunit_ids").equals(i==0?scenario.attackerArmyIds():scenario.defenderArmyIds()),"native "+sn+" explicit participant order mismatch");optionalInt(sr.get("selected_commander_character_id"),false,sn+".selected_commander_character_id");i32(sr.get("relation_kind_raw"),sn+".relation_kind_raw");
                for(String field:List.of("commander_dynamic_raw","side_dynamic_raw","target_conditionals_residual_raw","side_total_raw"))i64(sr.get(field),sn+"."+field);
                require(big(sr,"side_total_raw").equals(big(sr,"commander_dynamic_raw").add(big(sr,"side_dynamic_raw")).add(big(sr,"target_conditionals_residual_raw"))),"native "+sn+" partial arithmetic mismatch");
                if(sr.has("side_modifier_sources"))sideSources(sr.get("side_modifier_sources"),i,sn+".side_modifier_sources");if(sr.has("commander_source_inputs"))commanderInputs(sr.get("commander_source_inputs"),sn+".commander_source_inputs");if(sr.has("commander_sources"))commanderSources(sr.get("commander_sources"),i,sn+".commander_sources");
            }
            if(version==1)require(big(row,"synthetic_zero_roll_total_raw").equals(big(row,"base_nonreligious_accumulator_raw").add(sides.get(0).get("side_total_raw").bigIntegerValue()).subtract(sides.get(1).get("side_total_raw").bigIntegerValue())),"native "+name+" synthetic partial total mismatch");
            if(version==2)religionSources(row.get("religion_constructor_sources"),scenario,name+".religion_constructor_sources");
            if(nonreligious)nonreligiousSources(row.get("nonreligious_constructor_sources"),big(row,"base_nonreligious_accumulator_raw"),name+".nonreligious_constructor_sources");
            return row;
        }catch(IllegalArgumentException error){return unavailable(target,"contextual_advantage_fragment_invalid: "+error.getMessage(),version,nonreligious);}
    }
    private static void religionSources(JsonNode value,Scenario scenario,String name){
        ArrayNode sources=array(value,name);require(sources.size()==2,"native "+name+" must publish two ordered sources");
        for(int i=0;i<2;i++){
            String sn=name+"["+i+"]";ObjectNode row=object(sources.get(i),"side_index primary_public_cunit_id owner_character_id target_rite_id target_faith_id target_main_rite_id owner_rite_id owner_faith_id owner_rite_observed target_faith_unreformed owner_faith_matches_target selected applied source_key effect_advantage_points scale_raw signed_contribution_raw accumulator_before_raw accumulator_after_raw append_order skip_reason",sn);
            require(i32(row.get("side_index"),sn+".side_index")==i&&i32(row.get("primary_public_cunit_id"),sn+".primary_public_cunit_id")==(i==0?scenario.attackerArmyIds():scenario.defenderArmyIds()).get(0),"native "+sn+" primary participant binding mismatch");nonnegative(row.get("owner_character_id"),sn+".owner_character_id");
            for(String field:List.of("target_rite_id","target_faith_id","target_main_rite_id","owner_rite_id","owner_faith_id"))uint32(row.get(field),sn+"."+field,true,false);
            boolean observed=bool(row.get("owner_rite_observed"),sn+".owner_rite_observed");if(observed)bool(row.get("owner_faith_matches_target"),sn+".owner_faith_matches_target");else require(nil(row.get("owner_faith_matches_target"))&&nil(row.get("owner_rite_id"))&&nil(row.get("owner_faith_id")),"native "+sn+" unevaluated owner fields must be null");
            bool(row.get("target_faith_unreformed"),sn+".target_faith_unreformed");boolean selected=bool(row.get("selected"),sn+".selected");bool(row.get("applied"),sn+".applied");nullableText(row,"source_key",sn);conditionalField(row,"effect_advantage_points",selected,32,false,false,sn);
            for(String field:List.of("scale_raw","signed_contribution_raw","accumulator_before_raw","accumulator_after_raw"))i64(row.get(field),sn+"."+field);i32(row.get("append_order"),sn+".append_order");nullableText(row,"skip_reason",sn);
        }
    }
    private static void nonreligiousSources(JsonNode value,BigInteger base,String name){
        ArrayNode sources=array(value,name);require(sources.size()==NONRELIGIOUS.size(),"native "+name+" must publish thirteen ordered sources");BigInteger accumulator=BigInteger.ZERO;int append=0;
        for(int i=0;i<sources.size();i++){
            String stage=NONRELIGIOUS.get(i),sn=name+"["+i+"]";ObjectNode row=object(sources.get(i),"stage_order append_order stage side selected applied source_key effect_advantage_points scale_raw signed_contribution_raw accumulator_before_raw accumulator_after_raw skip_reason",sn);
            require(i32(row.get("stage_order"),sn+".stage_order")==i,"native "+sn+" constructor stage order or side mismatch");eq(row.get("stage"),stage,"native "+sn+" constructor stage order or side mismatch");eq(row.get("side"),side(stage),"native "+sn+" constructor stage order or side mismatch");
            boolean selected=bool(row.get("selected"),sn+".selected"),applied=bool(row.get("applied"),sn+".applied");require(!applied||selected,"native "+sn+" cannot apply an unselected source");conditionalField(row,"effect_advantage_points",selected,32,false,false,sn);if(selected)text(row.get("source_key"),sn+".source_key");else require(nil(row.get("source_key")),"native "+sn+" unselected source must null its key");
            for(String field:List.of("scale_raw","signed_contribution_raw","accumulator_before_raw","accumulator_after_raw"))i64(row.get(field),sn+"."+field);
            BigInteger contribution=applied?big(row,"effect_advantage_points").multiply(big(row,"scale_raw")):BigInteger.ZERO;if(side(stage).equals("defender"))contribution=contribution.negate();
            require(big(row,"signed_contribution_raw").equals(contribution),"native "+sn+" signed contribution mismatch");require(big(row,"accumulator_before_raw").equals(accumulator),"native "+sn+" accumulator_before mismatch");
            accumulator=accumulator.add(contribution).max(BigInteger.valueOf(-10000000)).min(BigInteger.valueOf(10000000));require(big(row,"accumulator_after_raw").equals(accumulator),"native "+sn+" per-source clamp mismatch");
            if(applied){require(i32(row.get("append_order"),sn+".append_order")==append&&nil(row.get("skip_reason")),"native "+sn+" applied append order or skip mismatch");append++;}else{require(nil(row.get("append_order")),"native "+sn+" non-applied append order must be null");text(row.get("skip_reason"),sn+".skip_reason");}
        }require(accumulator.equals(base),"native "+name+" final nonreligious accumulator mismatch");
    }
    private static void commanderInputs(JsonNode value,String name){
        if(nil(value))return;ObjectNode row=object(value,"selected_commander_character_id effective_martial own_primary_character_id opposing_primary_character_id province_context_raw32 relation_kind_raw army_gated_modifier_cache_present army_gated_modifier_cached_raw army_gated_modifier_source_army_id army_gated_modifier_resolved_army_id army_gated_modifier_used_null_army army_gated_modifier_gate_result primary_identity_matches gathering_flag_raw gathering_modifier_flag_1a5 gathering_rule_effect_points gathering_rule_source_key",name);
        for(String field:List.of("selected_commander_character_id","own_primary_character_id","opposing_primary_character_id","army_gated_modifier_source_army_id","army_gated_modifier_resolved_army_id"))nullableI32(row,field,name);
        for(String field:List.of("army_gated_modifier_cache_present","army_gated_modifier_used_null_army","army_gated_modifier_gate_result","gathering_modifier_flag_1a5"))nullableBool(row,field,name);
        uint32(row.get("province_context_raw32"),name+".province_context_raw32",true,true);require(nonnegative(row.get("gathering_flag_raw"),name+".gathering_flag_raw")<=255,"native "+name+".gathering_flag_raw must be uint8");
        JsonNode key=row.get("gathering_rule_source_key");require(nil(key)||key.isTextual(),"native "+name+".gathering_rule_source_key must be string or null");
        i32(row.get("effective_martial"),name+".effective_martial");i32(row.get("relation_kind_raw"),name+".relation_kind_raw");nullableI64(row,"army_gated_modifier_cached_raw",name);bool(row.get("primary_identity_matches"),name+".primary_identity_matches");nullableI32(row,"gathering_rule_effect_points",name);
    }
    private static void commanderSources(JsonNode value,int side,String name){
        if(nil(value))return;ArrayNode sources=array(value,name);require(sources.size()==COMMANDER.size(),"native "+name+" must publish seven ordered commander stages");
        for(int i=0;i<sources.size();i++){
            String sn=name+"["+i+"]";ObjectNode row=object(sources.get(i),Set.of("side_index","stage_order","source_kind","modifier_id","status","predicate_observed","selected","modifier_raw","contribution_raw","scale100000","accumulator_before_raw","accumulator_after_raw","skip_reason","source_provenance"),Set.of("opposing_primary_details","province_details"),sn);
            require(i32(row.get("side_index"),sn+".side_index")==side&&i32(row.get("stage_order"),sn+".stage_order")==i,"native "+sn+" commander stage order or side mismatch");eq(row.get("source_kind"),COMMANDER.get(i),"native "+sn+" commander stage order or side mismatch");
            if(!nil(row.get("modifier_id")))require(nonnegative(row.get("modifier_id"),sn+".modifier_id")<=65535,"native "+sn+".modifier_id must be uint16");token(row.get("status"),sn+".status","observed","unavailable");
            for(String field:List.of("predicate_observed","selected"))nullableBool(row,field,sn);for(String field:List.of("modifier_raw","contribution_raw","accumulator_before_raw","accumulator_after_raw"))nullableI64(row,field,sn);i64(row.get("scale100000"),sn+".scale100000");scale(row.get("scale100000"),sn+".scale100000");nullableText(row,"skip_reason",sn);text(row.get("source_provenance"),sn+".source_provenance");
            if(row.has("opposing_primary_details"))opposingDetails(row.get("opposing_primary_details"),sn+".opposing_primary_details");if(row.has("province_details"))provinceDetails(row.get("province_details"),sn+".province_details");
        }
    }
    private static void opposingDetails(JsonNode value,String name){
        if(nil(value))return;Set<String> refs=Set.of("selected_personal_rite_reference","opposing_primary_personal_rite_reference","selected_personal_faith_reference","opposing_primary_personal_faith_reference","selected_religion_reference","opposing_primary_religion_reference");
        Set<String> flags=Set.of("opposing_primary_character_used_fallback","selected_rite_used_fallback","opposing_primary_rite_used_fallback","rite_pair_valid","selected_faith_used_fallback","opposing_primary_faith_used_fallback","religion_references_equal");Set<String> keys=new java.util.HashSet<>(refs);keys.addAll(flags);keys.addAll(Set.of("directed_rite_hostility_level","hostility_factor_count","hostility_factor_raw","sources"));ObjectNode row=object(value,keys,Set.of(),name);
        for(String field:refs)uint32(row.get(field),name+"."+field,true,true);for(String field:flags)nullableBool(row,field,name);if(!nil(row.get("directed_rite_hostility_level")))require(nonnegative(row.get("directed_rite_hostility_level"),name+".directed_rite_hostility_level")<=255,"native "+name+".directed_rite_hostility_level must be uint8");nullableI32(row,"hostility_factor_count",name);nullableI64(row,"hostility_factor_raw",name);
        ArrayNode sources=array(row.get("sources"),name+".sources");require(sources.size()==2,"native "+name+".sources must publish two ordered modifiers");
        for(int i=0;i<2;i++){String sn=name+".sources["+i+"]";ObjectNode source=object(sources.get(i),"modifier_id cache_present modifier_raw selected predicate_observed contribution_raw skip_reason",sn);require(nonnegative(source.get("modifier_id"),sn+".modifier_id")==416+i,"native "+sn+" modifier order mismatch");for(String field:List.of("cache_present","selected","predicate_observed"))nullableBool(source,field,sn);for(String field:List.of("modifier_raw","contribution_raw"))nullableI64(source,field,sn);nullableText(source,"skip_reason",sn);}
    }
    private static void provinceDetails(JsonNode value,String name){
        if(nil(value))return;ObjectNode row=object(value,"selected_culture_reference province_culture_reference cache_present selected_culture_used_fallback province_culture_used_fallback category1_pillar_equal",name);for(String field:List.of("selected_culture_reference","province_culture_reference"))uint32(row.get(field),name+"."+field,true,true);for(String field:List.of("cache_present","selected_culture_used_fallback","province_culture_used_fallback","category1_pillar_equal"))nullableBool(row,field,name);
    }
    private static void sideSources(JsonNode value,int side,String name){
        if(nil(value))return;ArrayNode sources=array(value,name);
        for(int i=0;i<sources.size();i++){
            String sn=name+"["+i+"]";ObjectNode row=object(sources.get(i),"side_index source_slot source_modifier_id condition_observed selected modifier_raw contribution_raw scale100000 skip_reason opposite_side_index eligible_opposite_effects opposite_eligible_contribution_sum_raw",sn);
            require(i32(row.get("side_index"),sn+".side_index")==side,"native "+sn+" side binding mismatch");text(row.get("source_slot"),sn+".source_slot");require(nonnegative(row.get("source_modifier_id"),sn+".source_modifier_id")<=65535,"native "+sn+".source_modifier_id must be uint16");
            bool(row.get("condition_observed"),sn+".condition_observed");bool(row.get("selected"),sn+".selected");for(String field:List.of("modifier_raw","contribution_raw","opposite_eligible_contribution_sum_raw"))nullableI64(row,field,sn);i64(row.get("scale100000"),sn+".scale100000");scale(row.get("scale100000"),sn+".scale100000");nullableText(row,"skip_reason",sn);
            if(!nil(row.get("opposite_side_index")))require(i32(row.get("opposite_side_index"),sn+".opposite_side_index")==1-side,"native "+sn+" opposite side binding mismatch");
            if(!nil(row.get("eligible_opposite_effects"))){ArrayNode effects=array(row.get("eligible_opposite_effects"),sn+".eligible_opposite_effects");for(int j=0;j<effects.size();j++){String en=sn+".eligible_opposite_effects["+j+"]";ObjectNode effect=object(effects.get(j),"native_ledger_index effect_key flag88_raw flag89_raw contribution_raw",en);nonnegative(effect.get("native_ledger_index"),en+".native_ledger_index");text(effect.get("effect_key"),en+".effect_key");for(String f:List.of("flag88_raw","flag89_raw"))require(nonnegative(effect.get(f),en+"."+f)<=255,"native "+en+" effect flags must be uint8");i64(effect.get("contribution_raw"),en+".contribution_raw");}}
        }
    }
}

