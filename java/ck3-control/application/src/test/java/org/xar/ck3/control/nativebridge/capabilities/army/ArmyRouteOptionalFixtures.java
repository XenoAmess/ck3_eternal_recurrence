package org.xar.ck3.control.nativebridge.capabilities.army;

import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.ArrayList;
import java.util.List;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

final class ArmyRouteOptionalFixtures {
    private ArmyRouteOptionalFixtures() { }
    static ObjectNode route() {
        ObjectNode n=StrictJson.object().put("status","available").put("army_id",0).put("origin_province_id",12).put("target_province_id",14);
        n.putArray("route_province_ids").add(12).add(13).add(14);n.putObject("legacy_payload").put("keep",true);
        n.putObject("province_supply").put("native_carmy_id",5).put("owner_character_id",7).putObject("target").put("province_id",14).put("role","target");return n;
    }
    static ObjectNode supply() {
        return StrictJson.object().put("source","native_captured_target_land_supply_inputs").put("input_basis","captured_owner_and_target_province")
                .put("scale",100000).put("status","available").put("subject_army_id",0).put("subject_carmy_id",5).put("owner_character_id",7).put("province_id",14)
                .put("province_component_raw",0).put("loaded_gain_raw",100000).put("native_province_component_applicable",false).put("native_resupply_eligible",true)
                .put("current_inputs_ready",true).put("province_component_observation_ready",true).put("resupply_observation_ready",true)
                .putNull("unavailable_reason").putNull("province_component_unavailable_reason").putNull("resupply_unavailable_reason");
    }
    static ObjectNode loss() {
        return StrictJson.object().put("source","native_captured_target_loss_operands").put("scale",100000).put("status","available")
                .put("observation_ready",true).putNull("unavailable_reason").put("commander_used_native_fallback",false)
                .put("commander_raw_full_id",18).put("commander_resolved_full_id",18).put("commander_modifier_1a9_raw",-10000)
                .put("loaded_excess_slope_raw",1).put("loaded_min_loss_raw",2).put("loaded_max_loss_raw",3).put("loaded_divisor_floor_raw",4);
    }
    static ObjectNode county(boolean passes) {
        return StrictJson.object().put("schema_version",1).put("source","native_preview_first_edge_county_entry_condition")
                .put("input_basis","current_unit_and_preview_first_remaining_province").put("predicate_rva",0x24E2230).put("status","available").putNull("unavailable_reason")
                .put("subject_army_id",0).put("requested_target_province_id",14).put("source_province_id",12).put("target_province_id",13)
                .put("native_carmy_id",5).put("actor_character_id",7).put("mode",1).put("army_1d4_raw",0)
                .put("source_definition_1b_u8",1).put("target_definition_1b_u8",1).put("target_county_magic_3e0_u32",0x436F4461L)
                .put("source_county_present",true).put("target_county_present",true).put("county_objects_differ",true).put("native_condition_passes",passes)
                .put("inputs_observation_ready",true).put("native_condition_called",true).put("identity_before_after_match",true)
                .put("internal_subpredicates_observed",false).put("actual_loss_observed",false).put("source_county_identity","native:9007199254740993")
                .put("target_county_identity","native:18446744073709551615");
    }
    static ObjectNode adjacency(int count) {
        boolean unavailable=count<0,truncated=count>64;ObjectNode n=StrictJson.object().put("schema_version",1)
                .put("source","native_origin_province_map_node_rows_12004").put("input_basis","preview_origin_province_native_adjacency_rows")
                .put("status",unavailable?"unavailable":truncated?"truncated":"available").put("source_province_id",12)
                .put("native_count",count).put("published_row_limit",64).put("observed_count",unavailable?0:Math.min(count,64))
                .put("collection_complete",!unavailable&&!truncated).put("truncated",truncated).put("identity_before_after_match",!unavailable)
                .put("native_condition_evaluated_for_rows",false).put("route_legality_evaluated_for_rows",false);
        if(unavailable)n.put("unavailable_reason","origin_unavailable").putNull("source_province_identity").putNull("source_map_node_identity").putNull("adjacency_data_identity").putNull("rows");
        else {
            if(truncated)n.put("unavailable_reason","origin_adjacency_row_budget_exhausted");else n.putNull("unavailable_reason");
            n.put("source_province_identity","native:1").put("source_map_node_identity","native:2");
            if(count==0)n.putNull("adjacency_data_identity");else n.put("adjacency_data_identity","native:3");
            ArrayNode rows=n.putArray("rows");for(int i=0;i<Math.min(count,64);i++)rows.addObject().put("occurrence_index",i).put("target_province_id",13+i);
        }
        return n;
    }
    static ObjectNode stage(int index,Boolean returned) {
        ObjectNode n=StrictJson.object().put("call_count",returned==null?0:1);
        if(returned==null)return n.putNull("actual_caller_return_rva").putNull("argument_identity_matched").putNull("returned");
        return n.put("actual_caller_return_rva",new long[]{0x24E22B3L,0x24E22F1L,0x24E2348L}[index]).put("argument_identity_matched",true).put("returned",returned);
    }
    static ObjectNode trace(boolean finalPasses,Boolean source,Boolean first,Boolean second) {
        ObjectNode n=StrictJson.object().put("schema_version",1).put("source","same_preview_native_P_returns_12004")
                .put("status","available").putNull("unavailable_reason").put("hook_installed",true).put("scope_entered",true)
                .put("same_thread",true).put("order_valid",true).put("native_predicate_returned",true).put("final_condition_passes",finalPasses)
                .put("ignored_foreign_calls",0).put("ignored_nested_calls",4294967295L).put("additional_native_predicate_calls",0).put("neighbor_Q_observed",false);
        n.putArray("stages").add(stage(0,source)).add(stage(1,first)).add(stage(2,second));return n;
    }
    static ObjectNode relation(boolean returned,int war,boolean sample) {
        ObjectNode n=StrictJson.object().put("schema_version",1).put("source","native_original_relation_entry_return_12004")
                .put("status","available").putNull("unavailable_reason").put("call_count",1)
                .put("actual_bridge_caller_return_rva",new java.math.BigInteger("18446744073709551615"))
                .put("receiver_full_id",4294967295L).put("actor_full_id",0).put("argument_identity_matched",true).put("same_thread",true)
                .put("identity_before_after_match",true).put("returned",returned).putNull("auxiliary_identity")
                .put("sampled_relation_available",sample).put("unknown_or_inputs",true);
        if(sample) {
            n.putNull("sampled_relation_unavailable_reason").put("sampled_relation_identity","native:9007199254740993").put("sampled_relation_full_war_id",war);
            if(war==-1)n.putNull("sampled_selected_war_identity").putNull("sampled_selected_war_used_fallback").putNull("sampled_selected_war_byte_358_u8")
                    .putNull("sampled_direct_war_matches_aux").put("sampled_direct_war_gate",false);
            else n.put("sampled_selected_war_identity","native:18446744073709551615").put("sampled_selected_war_used_fallback",true)
                    .put("sampled_selected_war_byte_358_u8",0).put("sampled_direct_war_matches_aux",true).put("sampled_direct_war_gate",true);
        } else n.put("sampled_relation_unavailable_reason","sample_unavailable").putNull("sampled_relation_identity").putNull("sampled_relation_full_war_id")
                .putNull("sampled_selected_war_identity").putNull("sampled_selected_war_used_fallback").putNull("sampled_selected_war_byte_358_u8")
                .putNull("sampled_direct_war_matches_aux").putNull("sampled_direct_war_gate");
        return n;
    }
    static ObjectNode attach(ObjectNode supply,ObjectNode county) {
        ObjectNode route=route();if(supply!=null)((ObjectNode)route.path("province_supply").get("target")).set("captured_target_land_supply_inputs_v1",supply);
        if(county!=null)route.set("county_entry_condition_v1",county);return route;
    }
    static List<ObjectNode> validCases() {
        List<ObjectNode> result=new ArrayList<>();result.add(route());
        ObjectNode nulls=route();nulls.putNull("county_entry_condition_v1");((ObjectNode)nulls.path("province_supply").get("target")).putNull("captured_target_land_supply_inputs_v1");result.add(nulls);
        result.add(attach(supply(),county(true)));
        for(int count:new int[]{-1,0,2,65}) { ObjectNode county=county(false);county.set("origin_adjacency_v1",adjacency(count));result.add(attach(supply(),county)); }
        ObjectNode nullAdj=county(false);nullAdj.putNull("origin_adjacency_v1");result.add(attach(null,nullAdj));
        ObjectNode partial=supply().put("status","partial").put("current_inputs_ready",false).put("resupply_observation_ready",false)
                .putNull("native_resupply_eligible").putNull("loaded_gain_raw").put("resupply_unavailable_reason","resupply_unknown").put("unavailable_reason","resupply_unknown");result.add(attach(partial,null));
        ObjectNode resupplyOnly=supply().put("status","partial").put("current_inputs_ready",false).put("province_component_observation_ready",false)
                .putNull("native_province_component_applicable").putNull("province_component_raw").put("province_component_unavailable_reason","component_unknown")
                .put("unavailable_reason","component_unknown");result.add(attach(resupplyOnly,null));
        ObjectNode unavailable=supply().put("status","unavailable").put("current_inputs_ready",false).put("province_component_observation_ready",false)
                .put("resupply_observation_ready",false).put("province_component_unavailable_reason","component_unknown").put("resupply_unavailable_reason","resupply_unknown")
                .put("unavailable_reason","component_unknown").putNull("province_component_raw").putNull("native_province_component_applicable").putNull("native_resupply_eligible");result.add(attach(unavailable,null));
        ObjectNode withLoss=supply();withLoss.set("loss_adjustment_operands_v1",loss());result.add(attach(withLoss,null));
        ObjectNode nullLoss=supply();nullLoss.putNull("loss_adjustment_operands_v1");result.add(attach(nullLoss,null));
        ObjectNode fallback=supply();fallback.set("loss_adjustment_operands_v1",loss().put("commander_used_native_fallback",true).put("commander_raw_full_id",-1));result.add(attach(fallback,null));
        ObjectNode unknownLoss=loss().put("status","unavailable").put("observation_ready",false).put("unavailable_reason","loss_unknown")
                .putNull("commander_used_native_fallback").putNull("commander_raw_full_id").putNull("commander_resolved_full_id").putNull("commander_modifier_1a9_raw");
        ObjectNode lossFamily=supply();lossFamily.set("loss_adjustment_operands_v1",unknownLoss);result.add(attach(lossFamily,null));
        for(int variant=0;variant<6;variant++) {
            boolean finalPasses=variant==0;ObjectNode county=county(finalPasses),trace=trace(finalPasses,true,true,true);
            if(variant==2)trace=trace(false,false,null,null);
            if(variant==3) { trace=trace(false,null,null,null);county.put("source_definition_1b_u8",0); }
            if(variant==4) { trace.put("status","unavailable").put("unavailable_reason","trace_unknown").put("same_thread",false).putNull("final_condition_passes");
                ((ObjectNode)trace.path("stages").get(0)).put("call_count",2).put("argument_identity_matched",false); }
            if(variant==5) ((ObjectNode)trace.path("stages").get(0)).set("relation_inputs_v1",relation(true,-1,true));
            county.set("predicate_trace_v1",trace);county.put("internal_subpredicates_observed",variant!=3&&variant!=4);result.add(attach(null,county));
        }
        for(int war:new int[]{-1,0,17}) {
            ObjectNode county=county(false),trace=trace(false,false,null,null);
            ((ObjectNode)trace.path("stages").get(0)).set("relation_inputs_v1",relation(false,war,true));county.set("predicate_trace_v1",trace);
            county.put("internal_subpredicates_observed",true);result.add(attach(null,county));
        }
        ObjectNode noInput=county(false).put("status","unavailable").put("unavailable_reason","inputs_unknown").put("inputs_observation_ready",false)
                .put("native_condition_called",false).put("identity_before_after_match",false).putNull("native_condition_passes");result.add(attach(null,noInput));
        ObjectNode nullCount=county(false);nullCount.set("origin_adjacency_v1",adjacency(-1).putNull("native_count"));result.add(attach(null,nullCount));
        ObjectNode same=county(false),sameTrace=trace(false,false,null,null);ObjectNode sameRelation=relation(false,-1,false).put("actor_full_id",4294967295L);
        ((ObjectNode)sameTrace.path("stages").get(0)).set("relation_inputs_v1",sameRelation);same.set("predicate_trace_v1",sameTrace);same.put("internal_subpredicates_observed",true);result.add(attach(null,same));
        ObjectNode uncalled=county(false).put("source_definition_1b_u8",0),uncalledTrace=trace(false,null,null,null);
        ObjectNode uncalledRelation=relation(false,-1,false).put("status","unavailable").put("unavailable_reason","relation_not_called").put("call_count",0)
                .putNull("actual_bridge_caller_return_rva").putNull("receiver_full_id").putNull("actor_full_id").putNull("returned").putNull("identity_before_after_match");
        ((ObjectNode)uncalledTrace.path("stages").get(0)).set("relation_inputs_v1",uncalledRelation);uncalled.set("predicate_trace_v1",uncalledTrace);result.add(attach(null,uncalled));
        return List.copyOf(result);
    }
    static OpportunityJson.Obj json(ObjectNode n) { return (OpportunityJson.Obj)OpportunityJson.parse(StrictJson.canonical(n,8*1024*1024)); }
}
