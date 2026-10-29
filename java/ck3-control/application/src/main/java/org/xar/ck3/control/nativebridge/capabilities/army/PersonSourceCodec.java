package org.xar.ck3.control.nativebridge.capabilities.army;

import static org.xar.ck3.control.nativebridge.capabilities.army.PersonCurrentJson.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Set;

/** Finite 2922680 object graph, preserving occurrence order and independent primary readiness. */
final class PersonSourceCodec {
    private static final Set<String> MAPPED=Set.of("mapped_first_full_id_match","mapped_default_wrong_magic","mapped_default_no_match","mapped_default_empty_header");
    private PersonSourceCodec() { }
    private static Row record(JsonNode value,String field){return new Row(value,field).booleans(false,"ready").strings(true,"reason");}
    private static ObjectNode finish(Row r,boolean mappedReason){ObjectNode n=r.done();if(yes(n,"ready"))need(s(n,"reason")==null||mappedReason&&MAPPED.contains(s(n,"reason")),r.field+" ready observation retains unavailable reason");return n;}
    static JsonNode resolution(JsonNode raw,String field) {
        ObjectNode n=finish(record(raw,field).strings(true,"registry_identity registry_slots_identity candidate_identity selected_identity")
            .numbers(32,true,true,"requested_full_id_u32 registry_count_u32 candidate_full_id_u32").strings(false,"selection"),false);
        need(selected(s(n,"selection"),"unavailable","fallback","mapped"),field+" unknown native resolution selection");return n;
    }
    static JsonNode pc(JsonNode raw,String field) {
        ObjectNode n=finish(record(raw,field).strings(true,"identity").numbers(32,false,true,"count_i32").booleans(true,"admitted")
            .numbers(64,false,false,"weight_q100000").child("properties",PersonCurrentJson::pcValues),true);
        need(UNIT.equals(i(n,"weight_q100000")),field+" native unit append differs");
        if(yes(n,"ready")&&yes(n,"admitted")){JsonNode block=n.get("properties");BigInteger count=i(n,"count_i32");need(exists(n,"identity")&&nonnegative(count)&&!block.isNull()&&exists(block,"keys_u16")&&exists(block,"values_q64")
            &&eq(count,BigInteger.valueOf(block.get("keys_u16").size()))&&eq(count,BigInteger.valueOf(block.get("values_q64").size())),field+" actual copied PC operands absent");}return n;
    }
    private static JsonNode membershipRow(JsonNode raw,String field){return finish(record(raw,field).strings(true,"key_identity").booleans(true,"admitted").numbers(32,true,false,"native_index"),true);}
    private static JsonNode membership(JsonNode raw,String field){
        Row r=record(raw,field).strings(true,"header_identity array_identity membership_array_identity").numbers(32,false,true,"count_i32 membership_count_i32").children("rows",PersonSourceCodec::membershipRow,true);
        JsonNode values=r.take("membership_identities");if(values.isNull())r.out.putNull("membership_identities");else {need(values.isArray(),field+" membership list/null required");var a=r.out.putArray("membership_identities");for(JsonNode value:values)a.add(text(value,field+".membership_identities",false,false));}return finish(r,false);
    }
    private static JsonNode probe(JsonNode raw,String field){return new Row(raw,field).numbers(32,true,false,"native_index").strings(true,"slot_identity").numbers(8,true,true,"control_u8").numbers(32,true,true,"key_u32").done();}
    private static JsonNode getter(JsonNode raw,String field){return finish(record(raw,field).strings(true,"table_identity end_slot_identity found_slot_identity result_identity")
        .numbers(32,true,true,"input_magic_u32 input_full_id_u32 hash_u32 selected_value_u32 result_magic_u32 result_full_id_u32")
        .numbers(8,true,true,"overflow_u8").numbers(32,false,true,"mask_i32").numbers(64,false,true,"start_index_i64").booleans(true,"admitted")
        .children("probes",PersonSourceCodec::probe,true).child("value_resolution",PersonSourceCodec::resolution),false);}
    private static JsonNode nested(JsonNode raw,String field){return finish(record(raw,field).strings(true,"object_identity").numbers(32,true,true,"selector_id_u32").booleans(true,"matched")
        .child("primary_pc",PersonSourceCodec::pc).child("membership",PersonSourceCodec::membership).numbers(32,true,false,"native_index"),false);}
    private static JsonNode item(JsonNode raw,String field){return finish(record(raw,field).strings(true,"object_identity nested_array_identity").numbers(8,true,true,"enabled_3f0_u8").numbers(32,false,true,"nested_count_i32")
        .child("primary_pc",PersonSourceCodec::pc).child("membership",PersonSourceCodec::membership).children("nested",PersonSourceCodec::nested,true).numbers(32,true,false,"native_index"),false);}
    private static JsonNode source(JsonNode raw,String field){
        ObjectNode n=finish(record(raw,field).strings(true,"match_definition_identity item_container_identity item_array_identity")
            .numbers(32,true,true,"list_full_id_u32 match_id_u32").numbers(32,false,true,"item_count_i32").booleans(false,"direct_ready").booleans(true,"list_id_demanded")
            .child("resolution",PersonSourceCodec::resolution).child("getter",PersonSourceCodec::getter).children("items",PersonSourceCodec::item,true).numbers(32,true,false,"native_index"),false);
        need(eq(i(n,"list_full_id_u32"),i(n.get("resolution"),"requested_full_id_u32")),field+" physical full ID changed actual lookup input");return n;
    }
    private static JsonNode outer(JsonNode raw,String field){
        ObjectNode n=finish(record(raw,field).strings(true,"current_game_data_identity source_list_array_identity").numbers(32,true,true,"list_full_id_u32")
            .numbers(16,false,true,"cached_date_c7ce_i16").numbers(32,false,true,"raw_date_c7c8_i32 derived_year_i32 current_date_i32 source_list_count_i32")
            .booleans(false,"known_no_contribution primary_ready").booleans(true,"list_id_demanded date_admitted").strings(false,"date_branch")
            .child("resolution",PersonSourceCodec::resolution).children("sources",PersonSourceCodec::source,true).numbers(32,true,false,"native_index"),false);
        need(eq(i(n,"list_full_id_u32"),i(n.get("resolution"),"requested_full_id_u32")),field+" physical full ID changed lookup input");
        need(selected(s(n,"date_branch"),"unavailable","expired","not_expired","no_current_date_required"),field+" unknown source date branch");
        if(exists(n,"derived_year_i32")){BigInteger cached=i(n,"cached_date_c7ce_i16"),date=i(n,"raw_date_c7c8_i32"),expected=null;
            if(cached!=null&&cached.signum()>=0)expected=cached;else if(cached!=null&&date!=null){int wrapped=date.intValue()-43800000;expected=BigInteger.valueOf(wrapped/8760);}
            need(eq(i(n,"derived_year_i32"),expected),field+" decoded native calendar year differs");}return n;
    }
    private static JsonNode append(JsonNode raw,String field){
        Row core=record(raw,field).strings(true,"identity").numbers(32,false,true,"count_i32").booleans(true,"admitted")
            .numbers(64,false,false,"weight_q100000").child("properties",PersonCurrentJson::pcValues);
        core.strings(false,"kind").numbers(32,true,false,"outer_index source_index item_index").numbers(32,true,true,"nested_index descriptor_index");
        ObjectNode n=finish(core,true);need(selected(s(n,"kind"),"item_primary","nested_primary","item_mapped","nested_mapped"),field+" unknown append kind");need(yes(n,"admitted"),field+" flat occurrence is not an admitted source call");
        need(UNIT.equals(i(n,"weight_q100000")),field+" native unit append differs");if(yes(n,"ready")){JsonNode block=n.get("properties");BigInteger count=i(n,"count_i32");need(exists(n,"identity")&&nonnegative(count)&&!block.isNull()&&exists(block,"keys_u16")&&exists(block,"values_q64")&&eq(count,BigInteger.valueOf(block.get("keys_u16").size()))&&eq(count,BigInteger.valueOf(block.get("values_q64").size())),field+" ready admitted append lacks PC operands");}return n;
    }
    static ObjectNode following(JsonNode raw,String field){
        Row r=base(raw,field,"xar.ck3.person-following-2922680-12004-v1").booleans(false,"ready").strings(true,"reason character_identity selected_model_identity destination_pc_identity character_context_1c0_identity character_gate_1d0_identity list_header_identity list_array_identity source_operand_identity source_operand_reason")
            .numbers(32,true,true,"character_id").numbers(32,false,true,"list_count_i32").booleans(false,"source_operand_ready primary_ready").strings(false,"header_selection")
            .child("rite_resolution",PersonSourceCodec::resolution).child("context_resolution",PersonSourceCodec::resolution).child("operand_rite_resolution",PersonSourceCodec::resolution)
            .children("rows",PersonSourceCodec::outer,true).children("append_occurrences",PersonSourceCodec::append,false);
        ObjectNode n=finish(r,false);PersonConditionalCodec.prefixCount(n,"list_count_i32","rows",field);
        if(yes(n,"primary_ready")||yes(n,"ready"))exactCount(n,"list_count_i32","rows",field);
        if(yes(n,"primary_ready")){for(JsonNode row:n.get("rows"))need(yes(row,"primary_ready"),field+" unavailable primary outer row");for(JsonNode row:n.get("append_occurrences"))if(selected(s(row,"kind"),"item_primary","nested_primary"))need(yes(row,"ready"),field+" unavailable primary PC");}
        if(yes(n,"ready"))need(yes(n,"primary_ready")&&allReady(n.get("rows"))&&allReady(n.get("append_occurrences")),field+" complete helper retains unavailable occurrence");return n;
    }
}
