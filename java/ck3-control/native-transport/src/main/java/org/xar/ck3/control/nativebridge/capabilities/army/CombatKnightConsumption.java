package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.military.combatwire.KnightStatConsumptionCodec;
import static org.xar.ck3.control.nativebridge.capabilities.army.CombatProjectionJson.*;

/** Original normalized per-Ci consumption projection, including owned postimage selection. */
public final class CombatKnightConsumption {
    private CombatKnightConsumption() { }
    private static final String STAGE="native_wrapper_consumed_per_ci_contexts";
    private static final String[] CACHE={"max_size","siege_value_raw","damage_raw","toughness_raw","pursuit_raw","screen_raw"};
    private static final String[] STATS={"effective_max_size","effective_siege_raw","effective_damage_raw","effective_toughness_raw","effective_pursuit_raw","effective_screen_raw"};
    public static Optional<Obj> project(Obj normalizedLeaf) {return project(node(normalizedLeaf));}
    static Optional<Obj> project(JsonNode value) {
        JsonNode normalized=KnightStatConsumptionCodec.normalize(value,"combat_public.knight_stat_consumption_v1");if(nil(normalized))return Optional.empty();
        var n=object(normalized);var result=obj();result.set("source_schema",n.get("schema").deepCopy());copy(n,result,"build_version executable_sha256 configured observer_installed oldest_available_sequence latest_sequence overwritten_events reason");
        var events=result.putArray("events");int associated=0;for(var event:array(n.get("events"))){events.add(event(object(event)));if(yes(event.get("entry_association_proven")))associated++;}
        result.put("physical_entry_associated_event_count",associated).put("entry_association_proven",associated>0).put("historical_stage_equivalence_proven",false).put("actual_model_write_performed",false).put("full_person_ready",false).put("full_entry_ready",false);return Optional.of(immutable(result));
    }
    private record Modifier(Optional<BigInteger> value,ObjectNode detail) { }
    private static Modifier modifier(ObjectNode row,int key,ObjectNode prepared) {
        JsonNode pc=prepared==null?row.get("consumed_pc"):prepared;var detail=obj();copy(row,detail,"property_key operand_raw selected_character_id selected_character_identity context_identity context_matches_preparation owner_matches_preparation pc_matches_preparation_post");detail.set("consumed_pc_identity",row.get("consumed_pc").get("identity").deepCopy());if(prepared!=null)detail.set("preparation_source_pc_identity",prepared.get("identity").deepCopy());
        if(integer(row.get("operand_raw")).signum()==0){detail.put("branch","zero_operand_skips_property").putArray("lookups");return new Modifier(Optional.empty(),detail);}
        JsonNode block=pc.get("properties");if(!yes(pc.get("ready"))||nil(block)){detail.put("branch","consumed_pc_unavailable");detail.set("reason",pc.get("reason").deepCopy());detail.putArray("lookups");return new Modifier(Optional.empty(),detail);}
        var lookup=CombatKnightKernel.lookup(CombatKnightKernel.container(block.get("keys_u16"),block.get("values_q64"),pc.get("count_i32")),key);
        detail.put("branch",prepared==null?"actual_consumed_pc_mode0":"transferred_owned_preparation_pc_mode0");detail.set("lookups",node(lookup.detail()).get("lookups"));detail.set("missing_inputs",node(lookup.detail()).get("missing_inputs"));return new Modifier(lookup.value(),detail);
    }
    static ObjectNode event(ObjectNode event) {
        var contexts=array(event.get("contexts"));Map<Integer,ObjectNode> byKey=new LinkedHashMap<>();for(var row:contexts)byKey.put(integer(row.get("property_key")).intValueExact(),object(row));
        var owned=CombatKnightOwnedPreparation.owned(event);Map<Integer,ObjectNode> transferred=new LinkedHashMap<>();var transferLedger=obj().arrayNode();
        for(var row:contexts) {
            JsonNode lineage=row.get("installed_transfer_lineage");boolean selected=lineage!=null&&lineage.isObject()&&lineage.has("physical_postimage_owned_at_consumption");
            JsonNode records=lineage!=null&&lineage.isObject()?lineage.path("capture_at_consumption").get("records"):null;if(records!=null&&records.isArray())for(var record:records)selected|=record.has("physical_postimage");
            if(selected){var t=CombatKnightOwnedPreparation.transfer(object(row),event.get("thread_id"));transferLedger.add(node(t.proof()));int key=integer(row.get("property_key")).intValueExact();if(t.pc().isPresent()&&!owned.overrides().containsKey(key))transferred.put(key,t.pc().orElseThrow());}
        }
        List<BigInteger> modifiers=new ArrayList<>(),operands=new ArrayList<>(),selectedIds=new ArrayList<>();var details=obj().arrayNode();
        for(int key=0xc1;key<=0xc9;key++) {
            var row=byKey.get(key);if(row==null){modifiers.add(null);operands.add(null);selectedIds.add(null);details.addObject().put("property_key",key).put("branch","native_context_unobserved");continue;}
            Modifier m;
            if(owned.overrides().containsKey(key)){var over=owned.overrides().get(key);m=new Modifier(over.value(),node(over.detail()));}
            else if(transferred.containsKey(key)){m=modifier(row,key,transferred.get(key));m.detail().put("historical_postimage_selected",true).put("preparation_capture_source","same_ci_owned_completed_preparation_pc_through_copied_transfer");if(row.has("preparation_stage_lineage"))m.detail().set("preparation_stage_lineage",row.get("preparation_stage_lineage").deepCopy());}
            else {m=modifier(row,key,null);if(row.has("preparation_stage_lineage")){m.detail().set("preparation_stage_lineage",row.get("preparation_stage_lineage").deepCopy());m.detail().put("historical_postimage_selected",false);}}
            if(row.has("installed_transfer_lineage")){JsonNode l=row.get("installed_transfer_lineage");m.detail().set("installed_transfer_lineage",l.deepCopy());m.detail().put("installed_identity_associated",!nil(l)&&yes(l.get("installed_identity_associated"))).put("transfer_numeric_postimage_selected",transferred.containsKey(key));}
            modifiers.add(m.value().orElse(null));operands.add(nil(row.get("operand_raw"))?null:integer(row.get("operand_raw")));selectedIds.add(nil(row.get("selected_character_id"))?null:integer(row.get("selected_character_id")));details.add(m.detail());
        }
        BigInteger selected=selectedIds.getFirst();if(selected!=null)for(var id:selectedIds)if(!selected.equals(id)){selected=null;break;}
        var keys=obj().arrayNode();for(int key=0xc1;key<=0xc9;key++)keys.add(key);var carrier=obj();values(carrier,"modifiers",modifiers);
        var context=CombatKnightKernel.container(keys,carrier.get("modifiers"),obj().numberNode(9));String stage=!transferred.isEmpty()?"actual4_consumed_ci_with_owned_transferred_preparation_pc":!owned.overrides().isEmpty()?"actual4_consumed_ci_with_owned_six_stage_postimage":STAGE;
        var selectedSource=obj().put("source_kind","per_ci_consumed_native_pc_projection").put("shared_native_context_claimed",false);selectedSource.set("consumed_contexts",contexts.deepCopy());
        var external=obj().put("source_family","actual4_2c06d10_2c06ae0");copy(event,external,"output_cache_identity");external.set("capture_sequence",event.get("sequence").deepCopy());
        var calculation=CombatKnightKernel.compute(new CombatKnightKernel.Input(CombatKnightKernel.optional(event.get("linked_character_id")),CombatKnightKernel.optional(event.get("linked_prowess_points")),STAGE,Optional.ofNullable(selected),stage,context,
                operands.stream().map(Optional::ofNullable).toList(),CombatKnightKernel.optional(event.get("loaded_damage_multiplier")),CombatKnightKernel.optional(event.get("loaded_toughness_multiplier")),immutable(selectedSource),immutable(external)));
        ObjectNode projected=null;if(calculation.statCache().isPresent()){projected=obj();var stats=node(calculation.statCache().orElseThrow());for(int i=0;i<CACHE.length;i++)projected.set(CACHE[i],stats.get(STATS[i]).deepCopy());}
        JsonNode observed=event.get("observed_output"),physical=event.get("physical_entry_writeback");boolean compare=calculation.ready()&&yes(observed.get("ready")),physicalReady=calculation.ready()&&!nil(physical)&&yes(physical.get("entry_cache").get("ready"));
        var result=obj();copy(event,result,"sequence thread_id observed_date_raw origin wrapper_caller_return_rva regiment_id target_province_id linked_character_id linked_character_identity output_cache_identity native_return_identity entry_association_proven");values(result,"selected_character_ids",selectedIds);nullable(result,"selected_character_id",selected);result.put("ready",calculation.ready()).put("source_stage",stage);strings(result,"missing_inputs",calculation.missing());values(result,"modifier_raw",modifiers);values(result,"operand_raw",operands);result.set("property_inputs",details);result.set("consumed_contexts",contexts.deepCopy());nullable(result,"projected_effectiveness_raw",calculation.effectiveness().orElse(null));result.set("projected_output",projected==null?obj().nullNode():projected);result.set("calculation_ledger",node(calculation.ledger()));result.set("observed_output",observed.deepCopy());result.put("comparison_ready",compare);var matches=matches(projected,observed,compare);result.set("field_matches",matches);if(compare)result.put("matches_observed_output",all(matches));else result.putNull("matches_observed_output");
        result.set("physical_entry_writeback",nil(physical)?obj().nullNode():physical.deepCopy());result.put("physical_entry_comparison_ready",physicalReady);var pm=matches(projected,nil(physical)?null:physical.get("entry_cache"),physicalReady);result.set("physical_entry_field_matches",pm);if(physicalReady)result.put("projection_matches_physical_entry_cache",all(pm));else result.putNull("projection_matches_physical_entry_cache");result.put("wrapper_output_physical_comparison_ready",!nil(physical)&&yes(physical.get("wrapper_output_comparison_ready")));result.set("wrapper_output_matches_physical_entry_cache",nil(physical)?obj().nullNode():physical.get("wrapper_output_matches_entry_cache").deepCopy());result.put("historical_stage_equivalence_proven",false).put("shared_native_context_claimed",false).put("actual_model_write_performed",false).put("full_person_ready",false).put("full_entry_ready",false);
        boolean preparation=false,transfer=false;for(var row:contexts){preparation|=row.has("preparation_stage_lineage")||row.has("preparation_capture_at_consumption");transfer|=row.has("installed_transfer_lineage");}
        if(preparation){var join=result.putObject("preparation_stage_join");keyLists(join,owned.overrides().keySet());join.set("owned_capture_compositions",owned.ledger());join.put("source","same_ci_owned_preparation_capture_at_consumption").put("later_current_query_used",false).put("original_operands_preserved",true).put("installed_model_transfer_inferred",false).put("original_entry_invocation_inferred",false);}
        if(transfer){var join=result.putObject("installed_transfer_stage_join");var associated=join.putArray("associated_property_keys");var unmatched=join.putArray("unmatched_property_keys");var inputs=join.putArray("property_inputs");List<Integer> assoc=new ArrayList<>();for(var row:contexts){var l=row.get("installed_transfer_lineage");if(nil(l))continue;int key=integer(row.get("property_key")).intValueExact();if(yes(l.get("installed_identity_associated"))){assoc.add(key);associated.add(key);}var input=inputs.addObject();copy(row,input,"property_key selected_character_id selected_character_identity");input.set("consumed_context_identity",row.get("context_identity").deepCopy());input.put("installed_identity_associated",yes(l.get("installed_identity_associated")));input.set("lineage",l.deepCopy());}for(int key=0xc1;key<=0xc9;key++)if(!assoc.contains(key))unmatched.add(key);join.put("source","same_ci_owned_installed_transfer_before_getter").put("later_current_query_used",false).put("generic_postimages_complete",false).put("numeric_postimage_substitution_performed",!transferred.isEmpty()).put("original_operands_preserved",true).put("entry_association_inferred",false);}
        if(!transferLedger.isEmpty()){var join=result.putObject("installed_transfer_pc_stage_join");keyLists(join,transferred.keySet());join.set("property_inputs",transferLedger);join.put("source","same_ci_owned_completed_preparation_pc_through_copied_transfer").put("later_current_query_used",false).put("original_operands_preserved",true).put("generic_postimages_complete",false).put("full_person_ready",false).put("full_entry_ready",false);}
        return result;
    }
    private static void keyLists(ObjectNode n,java.util.Set<Integer> keys) {var matched=n.putArray("historical_property_keys");var unmatched=n.putArray("unmatched_property_keys");for(int k=0xc1;k<=0xc9;k++)if(keys.contains(k))matched.add(k);else unmatched.add(k);}
    private static ObjectNode matches(ObjectNode projected,JsonNode observed,boolean ready){var matches=obj();for(String field:CACHE)if(ready)matches.put(field,eq(projected.get(field),observed.get(field)));else matches.putNull(field);return matches;}
    private static boolean all(ObjectNode n){for(var value:n)if(!yes(value))return false;return true;}
}
